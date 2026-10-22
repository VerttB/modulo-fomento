import csv
import unicodedata
from functools import lru_cache
from pathlib import Path


def normalizar_municipio(nome: str) -> str:
    decomposed = unicodedata.normalize("NFKD", nome.casefold())
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(without_accents.split())


@lru_cache(maxsize=4)
def carregar_populacao_municipios(caminho: str) -> dict[str, dict[str, str | int]]:
    municipios: dict[str, dict[str, str | int]] = {}
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        for row in csv.DictReader(arquivo, delimiter=";"):
            nome = (row.get("Município") or "").strip()
            if not nome:
                continue
            try:
                populacao = int((row.get("População estimada") or "").strip())
            except ValueError:
                populacao = 0
            municipios[normalizar_municipio(nome)] = {
                "municipio": nome,
                "gentilico": (row.get("Gentílico") or "").strip(),
                "populacao_estimada": populacao,
            }
    return municipios
