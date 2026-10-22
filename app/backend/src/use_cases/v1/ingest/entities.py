from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import AreaConhecimentoTipo
from src.models import (
    AreaConhecimento,
    Departamento,
    Instituicao,
    PalavraChave,
    Projeto,
    TerritorioIdentidade,
    Unidade,
)
from src.services.ingest_reader import normalizar, texto_linha
from src.services.privacidade import sanitizar_texto_livre


def obter_area(
    db: Session,
    termo: str | None,
    tipo: AreaConhecimentoTipo,
    pai: AreaConhecimento | None,
) -> tuple[AreaConhecimento | None, bool]:
    if not termo:
        return None, False
    termo_normalizado = normalizar(termo)
    pai_id = pai.id if pai else None
    area = db.scalar(
        select(AreaConhecimento).where(
            AreaConhecimento.tipo == tipo,
            AreaConhecimento.termo_normalizado == termo_normalizado,
            AreaConhecimento.pai_id == pai_id,
        )
    )
    if area:
        return area, False
    area = AreaConhecimento(
        termo=termo, termo_normalizado=termo_normalizado, tipo=tipo, pai_id=pai_id
    )
    db.add(area)
    db.flush()
    return area, True


def obter_territorio_identidade(
    db: Session, nome: str | None
) -> TerritorioIdentidade | None:
    if not nome:
        return None
    normalizado = normalizar(nome)
    territorio = db.scalar(
        select(TerritorioIdentidade).where(
            TerritorioIdentidade.nome_normalizado == normalizado
        )
    )
    if territorio is None:
        territorio = TerritorioIdentidade(nome=nome, nome_normalizado=normalizado)
        db.add(territorio)
        db.flush()
    return territorio


def obter_instituicao(
    db: Session, nome: str | None, cep: str | None, sigla: str | None
) -> Instituicao:
    instituicao = None
    if sigla:
        instituicao = db.scalar(select(Instituicao).where(Instituicao.sigla == sigla))
    if instituicao is None and nome:
        instituicao = db.scalar(select(Instituicao).where(Instituicao.nome == nome))
    if instituicao is None:
        instituicao = Instituicao(nome=nome, cep=cep, sigla=sigla)
        db.add(instituicao)
        db.flush()
    elif instituicao.sigla is None and sigla:
        instituicao.sigla = sigla
        db.flush()
    return instituicao


def obter_departamento(
    db: Session,
    nome: str | None,
    unidade: str | None,
    cep: str | None,
    instituicao_id,
    grande_area_id=None,
) -> Departamento:
    departamento = db.scalar(
        select(Departamento).where(
            Departamento.instituicao_id == instituicao_id,
            Departamento.nome == nome,
        )
    )
    if departamento is None:
        departamento = Departamento(
            nome=nome,
            unidade=unidade,
            cep=cep,
            instituicao_id=instituicao_id,
            grande_area_id=grande_area_id,
        )
        db.add(departamento)
        db.flush()
    elif departamento.grande_area_id is None and grande_area_id is not None:
        departamento.grande_area_id = grande_area_id
        db.flush()
    return departamento


def obter_unidade(
    db: Session, nome: str | None, cep: str | None, departamento: Departamento
) -> Unidade:
    if nome:
        unidade = db.scalar(select(Unidade).where(Unidade.nome == nome))
    else:
        unidade = db.scalar(
            select(Unidade)
            .join(Unidade.departamentos)
            .where(Unidade.nome.is_(None), Departamento.id == departamento.id)
        )
    if unidade is None:
        unidade = Unidade(nome=nome, cep=cep)
        unidade.departamentos.append(departamento)
        db.add(unidade)
        db.flush()
    elif departamento not in unidade.departamentos:
        unidade.departamentos.append(departamento)
        db.flush()
    return unidade


def obter_projeto(
    db: Session, nome: str | None, resumo: str | None, area_conhecimento_id
) -> tuple[Projeto, bool]:
    nome = sanitizar_texto_livre(nome)
    resumo = sanitizar_texto_livre(resumo)
    projeto = db.scalar(
        select(Projeto).where(Projeto.nome == nome, Projeto.resumo == resumo)
    )
    if projeto:
        if not projeto.area_conhecimento_id and area_conhecimento_id:
            projeto.area_conhecimento_id = area_conhecimento_id
        return projeto, False
    projeto = Projeto(nome=nome, resumo=resumo, area_conhecimento_id=area_conhecimento_id)
    db.add(projeto)
    db.flush()
    return projeto, True


def adicionar_palavras_chave(
    db: Session, row: list, indices: dict[str, int], projeto: Projeto
) -> int:
    criadas = 0
    for numero in range(1, 5):
        termo = texto_linha(row, indices, f"pal chave{numero}")
        if not termo:
            continue
        normalizado = normalizar(termo)
        palavra = db.scalar(
            select(PalavraChave).where(PalavraChave.termo_normalizado == normalizado)
        )
        if palavra is None:
            palavra = PalavraChave(termo=termo, termo_normalizado=normalizado)
            db.add(palavra)
            db.flush()
            criadas += 1
        if palavra not in projeto.palavras_chave:
            projeto.palavras_chave.append(palavra)
    return criadas
