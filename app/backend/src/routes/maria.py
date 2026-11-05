from uuid import UUID

from fastapi import APIRouter, Query
from src.schemas.maria import ConversationCreate, MessageCreate
from src.services import maria


router = APIRouter(prefix="/maria/conversations", tags=["Maria"])


@router.get("")
async def listar(offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=100)):
    return await maria.listar_conversas(offset, limit)


@router.post("", status_code=201)
async def criar(body: ConversationCreate):
    return await maria.criar_conversa(body.title)


@router.get("/{conversation_id}")
async def obter(conversation_id: UUID):
    return await maria.obter_conversa(conversation_id)


@router.get("/{conversation_id}/messages")
async def mensagens(conversation_id: UUID):
    return await maria.listar_mensagens(conversation_id)


@router.post("/{conversation_id}/messages", status_code=201)
async def enviar(conversation_id: UUID, body: MessageCreate):
    return await maria.enviar_mensagem(conversation_id, body.content)
