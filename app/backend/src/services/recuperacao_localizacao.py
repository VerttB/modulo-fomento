"""Recupera CEPs das linhas originais sem armazenar ou registrar CPFs."""

import hashlib
from collections import Counter
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.core.enums import IngestaoStatus
from src.core.exceptions import IngestFormatError
from src.models import Bolsa, Ingestao, IngestaoLinha, Instituicao, Projeto
from src.services.cep_lookup import normalizar_cep
from src.services.ingest_reader import ler_planilha, mapear_colunas, normalizar, parse_data, texto_linha
from src.services.privacidade import sanitizar_texto_livre
from src.use_cases.v1.ingest.persist_entities import cep_referencia


def verificar_arquivo(ingestao: Ingestao, arquivo: Path):
    if ingestao.status == IngestaoStatus.PROCESSANDO:
        raise IngestFormatError("Aguarde a ingestão terminar antes da recuperação.")
    if not ingestao.arquivo_sha256:
        raise IngestFormatError("A ingestão não possui checksum para verificar o arquivo.")
    with arquivo.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest.lower() != ingestao.arquivo_sha256.lower():
        raise IngestFormatError("O arquivo não corresponde ao checksum da ingestão.")
    linhas, epoch = ler_planilha(ingestao.nome_arquivo, arquivo)
    if not linhas:
        raise IngestFormatError("O arquivo está vazio.")
    return linhas, epoch, mapear_colunas(linhas[0])


def linha_confere(row, indices, epoch, bolsa, projeto_nome, instituicao_nome, instituicao_sigla):
    try:
        inicio = parse_data(texto_linha(row, indices, "data inicial"), epoch)
    except IngestFormatError:
        return False
    titulo = sanitizar_texto_livre(texto_linha(row, indices, "titulo do projeto"))
    instituicao = texto_linha(row, indices, "instituicao")
    sigla = texto_linha(row, indices, "sigla instituicao")
    mesmo_projeto = normalizar(titulo or "") == normalizar(projeto_nome or "")
    mesma_instituicao = (
        bool(sigla and instituicao_sigla and normalizar(sigla) == normalizar(instituicao_sigla))
        or bool(instituicao and instituicao_nome and normalizar(instituicao) == normalizar(instituicao_nome))
        or not (instituicao or sigla or instituicao_nome or instituicao_sigla)
    )
    return inicio == bolsa.quando_iniciou and mesmo_projeto and mesma_instituicao


def ceps_da_linha(row, indices):
    ceps = [normalizar_cep(texto_linha(row, indices, column))
            for column in ("cep unidade", "cep departamento", "cep instituicao")]
    return list(dict.fromkeys(cep for cep in ceps if cep))


def recuperar_ceps(db: Session, ingestao_id: UUID, arquivo: Path, aplicar: bool = False):
    ingestao = db.execute(select(Ingestao.nome_arquivo, Ingestao.arquivo_sha256, Ingestao.status).where(Ingestao.id == ingestao_id)).first()
    if not ingestao:
        raise IngestFormatError("Ingestão não encontrada.")
    linhas, epoch, indices = verificar_arquivo(ingestao, arquivo)
    query = (select(Bolsa.id, Bolsa.linha_origem, Bolsa.quando_iniciou, Bolsa.cep_referencia,
                    Projeto.nome.label("projeto_nome"), Instituicao.nome.label("instituicao_nome"),
                    Instituicao.sigla, IngestaoLinha.linha_origem.label("linha_rastreada"))
             .join(Projeto, Projeto.id == Bolsa.projeto_id)
             .join(Instituicao, Instituicao.id == Bolsa.instituicao_id)
             .outerjoin(IngestaoLinha, (IngestaoLinha.bolsa_id == Bolsa.id) & (IngestaoLinha.ingestao_id == Bolsa.ingestao_id))
             .where(Bolsa.ingestao_id == ingestao_id).order_by(Bolsa.id))
    resultados = Counter()
    updates = []
    alternativas = {}
    for bolsa in db.execute(query):
        resultados["bolsas_verificadas"] += 1
        numero = bolsa.linha_origem
        if not numero or numero != bolsa.linha_rastreada or numero < 2 or numero > len(linhas):
            resultados["linhas_sem_vinculo_confiavel"] += 1
            continue
        row = linhas[numero - 1]
        if not linha_confere(row, indices, epoch, bolsa, bolsa.projeto_nome, bolsa.instituicao_nome, bolsa.sigla):
            resultados["linhas_divergentes"] += 1
            continue
        alternativas[bolsa.id] = ceps_da_linha(row, indices)
        cep = cep_referencia(row, indices)
        if not cep:
            resultados["sem_cep_valido_na_origem"] += 1
        elif bolsa.cep_referencia:
            resultados["cep_existente_preservado"] += 1
        else:
            resultados["ceps_recuperaveis"] += 1
            updates.append((bolsa.id, cep))
    db.rollback()
    if aplicar:
        for inicio in range(0, len(updates), 500):
            for bolsa_id, cep in updates[inicio:inicio + 500]:
                changed = db.execute(update(Bolsa).where(Bolsa.id == bolsa_id, Bolsa.cep_referencia.is_(None)).values(cep_referencia=cep))
                resultados["ceps_atualizados"] += changed.rowcount
            db.commit()
    return dict(resultados), alternativas
