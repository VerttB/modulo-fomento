from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import PalavraChave, Projeto
from src.schemas import PalavraChaveCreate, PalavraChaveUpdate


def listar_palavras_chave(db: Session) -> list[PalavraChave]:
    return list(db.scalars(select(PalavraChave)))


def obter_palavra_chave(db: Session, resource_id: int) -> PalavraChave:
    recurso = db.get(PalavraChave, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Palavra-chave não encontrada.")
    return recurso


def criar_palavra_chave(db: Session, payload: PalavraChaveCreate) -> PalavraChave:
    recurso = PalavraChave(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_palavra_chave(db: Session, resource_id: int, payload: PalavraChaveUpdate) -> PalavraChave:
    recurso = obter_palavra_chave(db, resource_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_palavra_chave(db: Session, resource_id: int) -> None:
    recurso = obter_palavra_chave(db, resource_id)
    db.delete(recurso)
    db.commit()


def listar_palavras_do_projeto(db: Session, projeto_id: int) -> dict:
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise ResourceNotFoundError("Projeto não encontrado.")
    return {"projeto_id": projeto.id, "palavras_chave": projeto.palavras_chave}


def definir_palavras_do_projeto(db: Session, projeto_id: int, ids: list[int]) -> dict:
    projeto = db.get(Projeto, projeto_id)
    if projeto is None:
        raise ResourceNotFoundError("Projeto não encontrado.")
    ids_unicos = set(ids)
    palavras = list(db.scalars(select(PalavraChave).where(PalavraChave.id.in_(ids_unicos)))) if ids_unicos else []
    if len(palavras) != len(ids_unicos):
        raise ResourceNotFoundError("Uma ou mais palavras-chave não foram encontradas.")
    projeto.palavras_chave = palavras
    db.commit()
    db.refresh(projeto)
    return {"projeto_id": projeto.id, "palavras_chave": projeto.palavras_chave}
