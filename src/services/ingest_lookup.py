from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import PesquisadorStatus
from src.core.exceptions import ExternalLookupError
from src.models import Pesquisador

IDENTIFICADOR_URL = "https://simcc.uesc.br/v3/api/getIdentificadorCNPq"
PESQUISADOR_URL = "https://observatoriocti.secti.ba.gov.br/simcc/api/researchers"
TIMEOUT_API_SEGUNDOS = 20.0

CHAVES_LATTES = {
    "lattesid", "idlattes", "identificador", "identificadorcnpq", "identificador_cnpq",
    "idcnpq", "id_cnpq", "lattes", "id",
}


def _json(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text.strip() or None


def _extrair_identificador(payload: Any) -> str | None:
    if isinstance(payload, (str, int)):
        value = str(payload).strip()
        return value or None
    if isinstance(payload, list):
        for item in payload:
            value = _extrair_identificador(item)
            if value:
                return value
        return None
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_norm = "".join(char for char in key.casefold() if char.isalnum() or char == "_")
            if key_norm in CHAVES_LATTES and value not in (None, ""):
                return str(value).strip()
        for value in payload.values():
            if isinstance(value, (dict, list)):
                identifier = _extrair_identificador(value)
                if identifier:
                    return identifier
        if len(payload) == 1:
            value = next(iter(payload.values()))
            if isinstance(value, (str, int)):
                return str(value).strip() or None
    return None


def _extrair_perfil(payload: Any) -> tuple[str | None, str | None] | None:
    if isinstance(payload, list):
        for item in payload:
            profile = _extrair_perfil(item)
            if profile:
                return profile
        return None
    if isinstance(payload, dict):
        fields = {str(key).casefold(): value for key, value in payload.items()}
        name = fields.get("name") or fields.get("nome")
        city = fields.get("city") or fields.get("cidade")
        if name or city:
            return (
                str(name).strip() if name else None,
                str(city).strip() if city else None,
            )
        for value in payload.values():
            if isinstance(value, (dict, list)):
                profile = _extrair_perfil(value)
                if profile:
                    return profile
    return None


def consultar_pesquisador(
    client: httpx.Client, cpf: str
) -> tuple[str | None, str | None, str | None]:
    try:
        resposta_id = client.get(
            IDENTIFICADOR_URL,
            params={"cpf": cpf, "nomeCompleto": "", "dataNascimento": ""},
        )
        resposta_id.raise_for_status()
        lattes = _extrair_identificador(_json(resposta_id))
        if not lattes:
            return None, None, None

        try:
            resposta_perfil = client.get(PESQUISADOR_URL, params={"lattes_id": lattes})
            resposta_perfil.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code == httpx.codes.NOT_FOUND:
                # Researchers sem registro: salva só o lattes da rota do CPF.
                return lattes, None, None
            raise
        perfil = _extrair_perfil(_json(resposta_perfil))
        if perfil is None:
            return lattes, None, None
        return lattes, perfil[0], perfil[1]
    except httpx.HTTPError as error:
        raise ExternalLookupError(
            "Não foi possível consultar os serviços externos de identificação."
        ) from error


def salvar_pesquisador(
    db: Session,
    cpf: str,
    identificacao: tuple[str | None, str | None, str | None],
) -> tuple[Pesquisador, bool]:
    lattes, nome, cidade = identificacao
    # Busca por lattes (identificador único), não por CPF
    pesquisador = db.scalar(select(Pesquisador).where(Pesquisador.lattes == lattes)) if lattes else None
    criado = pesquisador is None
    if criado:
        pesquisador = Pesquisador()
        db.add(pesquisador)
    pesquisador.lattes = lattes or pesquisador.lattes
    pesquisador.nome = nome or pesquisador.nome
    pesquisador.cidade = cidade or pesquisador.cidade
    pesquisador.status = (
        PesquisadorStatus.APROVADO if nome or cidade else PesquisadorStatus.PENDENTE
    )
    db.flush()
    return pesquisador, criado
