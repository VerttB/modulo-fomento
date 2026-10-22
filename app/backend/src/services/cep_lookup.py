import logging
import re

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


def normalizar_cep(value: str | None) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 8:
        return None
    return f"{digits[:5]}-{digits[5:]}"


def consultar_cidade_por_cep(client: httpx.Client, cep: str) -> str | None:
    digits = re.sub(r"\D", "", cep)
    if len(digits) != 8:
        return None
    try:
        response = client.get(settings.via_cep_url.format(cep=digits))
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        logger.warning("Não foi possível resolver a cidade do CEP informado.")
        return None
    if not isinstance(payload, dict) or payload.get("erro"):
        return None
    city = payload.get("localidade")
    return str(city).strip() if city else None
