from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import PesquisadorStatus
from src.core.exceptions import ExternalLookupError
from src.models import Pesquisador
from src.services.ingest_reader import normalizar

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


def _extrair_url_foto(value: Any) -> str | None:
    if isinstance(value, str):
        url = value.strip()
        return url if url.startswith(("https://", "http://")) and len(url) <= 2048 else None
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = normalizar(str(key)).replace("_", "").replace(" ", "")
            if normalized in {"url", "src", "href", "uri", "link"}:
                url = _extrair_url_foto(nested)
                if url:
                    return url
    return None


def _extrair_perfil_completo(
    payload: Any,
) -> tuple[str | None, str | None, str | None, str | None] | None:
    if isinstance(payload, list):
        for item in payload:
            profile = _extrair_perfil_completo(item)
            if profile:
                return profile
        return None
    if isinstance(payload, dict):
        fields = {str(key).casefold(): value for key, value in payload.items()}
        name = fields.get("name") or fields.get("nome")
        city = fields.get("city") or fields.get("cidade")
        territory = next(
            (
                value
                for key, value in fields.items()
                if (
                    normalizar(key) in {"territory", "territorio"}
                    or (
                        "territor" in normalizar(key)
                        and "identidade" in normalizar(key)
                    )
                    or "territory identity" in normalizar(key)
                )
            ),
            None,
        )
        photo_value = next(
            (
                value
                for key, value in fields.items()
                if any(
                    marker in normalizar(key).replace("_", "").replace(" ", "")
                    for marker in ("foto", "photo", "image", "imagem", "picture", "avatar")
                )
            ),
            None,
        )
        if isinstance(territory, dict):
            territory = territory.get("name") or territory.get("nome")
        photo_url = _extrair_url_foto(photo_value)
        if name or city or territory or photo_url:
            return (
                str(name).strip() if name else None,
                str(city).strip() if city else None,
                str(territory).strip() if territory else None,
                photo_url,
            )
        for value in payload.values():
            if isinstance(value, (dict, list)):
                profile = _extrair_perfil_completo(value)
                if profile:
                    return profile
    return None


def _extrair_perfil(payload: Any) -> tuple[str | None, str | None, str | None] | None:
    profile = _extrair_perfil_completo(payload)
    return profile[:3] if profile else None


def consultar_pesquisador(
    client: httpx.Client, cpf: str
) -> tuple[str | None, str | None, str | None, str | None]:
    try:
        resposta_id = client.get(
            settings.simcc_identificador_url,
            params={"cpf": cpf, "nomeCompleto": "", "dataNascimento": ""},
        )
        resposta_id.raise_for_status()
        lattes = _extrair_identificador(_json(resposta_id))
        if not lattes:
            return None, None, None, None

        nome, cidade, territorio = consultar_perfil_por_lattes(client, lattes)
        return lattes, nome, cidade, territorio
    except httpx.HTTPError as error:
        raise ExternalLookupError(
            "Não foi possível consultar os serviços externos de identificação."
        ) from error


def consultar_perfil_por_lattes(
    client: httpx.Client, lattes: str, collection: str | None = None
) -> tuple[str | None, str | None, str | None]:
    perfil = consultar_perfil_completo_por_lattes(client, lattes, collection)
    return perfil[:3] if perfil else (None, None, None)


def consultar_perfil_completo_por_lattes(
    client: httpx.Client, lattes: str, collection: str | None = None
) -> tuple[str | None, str | None, str | None, str | None] | None:
    try:
        params = {"lattes_id": lattes}
        if collection:
            params["collection"] = collection
        resposta_perfil = client.get(
            settings.simcc_researchers_url, params=params
        )
        resposta_perfil.raise_for_status()
    except httpx.HTTPStatusError as error:
        if error.response.status_code == httpx.codes.NOT_FOUND:
            return None
        raise ExternalLookupError(
            "Não foi possível consultar os dados públicos do pesquisador."
        ) from error
    except httpx.HTTPError as error:
        raise ExternalLookupError(
            "Não foi possível consultar os dados públicos do pesquisador."
        ) from error
    return _extrair_perfil_completo(_json(resposta_perfil))


def salvar_pesquisador(
    db: Session,
    identificacao: tuple[str | None, str | None, str | None, str | None],
    territorio_identidade_id: UUID | None = None,
) -> tuple[Pesquisador, bool]:
    lattes, nome, cidade, _territorio = identificacao
    # Busca por lattes (identificador único), não por CPF
    pesquisador = db.scalar(select(Pesquisador).where(Pesquisador.lattes == lattes)) if lattes else None
    criado = pesquisador is None
    if criado:
        pesquisador = Pesquisador()
        db.add(pesquisador)
    pesquisador.lattes = lattes or pesquisador.lattes
    pesquisador.nome = nome or pesquisador.nome
    pesquisador.cidade = cidade or pesquisador.cidade
    if territorio_identidade_id is not None:
        pesquisador.territorio_identidade_id = territorio_identidade_id
    pesquisador.status = (
        PesquisadorStatus.APROVADO if nome or cidade else PesquisadorStatus.PENDENTE
    )
    db.flush()
    return pesquisador, criado
