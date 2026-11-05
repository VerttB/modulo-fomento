from uuid import UUID

import httpx

from src.core.config import settings
from src.core.exceptions import ApplicationError, ExternalLookupError


class MariaResponseError(ApplicationError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


async def _request(method: str, path: str, **kwargs):
    try:
        async with httpx.AsyncClient(timeout=settings.maria_api_timeout_seconds) as client:
            response = await client.request(
                method, f"{settings.maria_api_url.rstrip('/')}{path}", **kwargs
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        if status in (404, 409, 422, 429):
            raise MariaResponseError(status, "A API Maria não conseguiu atender à solicitação.") from error
        raise ExternalLookupError("A API Maria está indisponível ou retornou um erro.") from error
    except (httpx.RequestError, ValueError) as error:
        raise ExternalLookupError("Não foi possível comunicar com a API Maria.") from error


async def listar_conversas(offset: int, limit: int):
    return await _request("GET", "/conversations", params={"offset": offset, "limit": limit})


async def criar_conversa(title: str | None):
    return await _request("POST", "/conversations", json={"title": title})


async def obter_conversa(conversation_id: UUID):
    return await _request("GET", f"/conversations/{conversation_id}")


async def listar_mensagens(conversation_id: UUID):
    return await _request("GET", f"/conversations/{conversation_id}/messages")


async def enviar_mensagem(conversation_id: UUID, content: str):
    return await _request("POST", f"/conversations/{conversation_id}/messages", json={"content": content})
