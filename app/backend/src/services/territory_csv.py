import csv
import io
from pathlib import Path

from src.core.exceptions import IngestFormatError
from src.services.ingest_reader import normalizar


def _column_index(headers: list[str], kind: str) -> int | None:
    normalized = [normalizar(value) for value in headers]
    if kind == "city":
        aliases = {"cidade", "municipio", "nome municipio", "nome cidade", "nm mun"}
        matches = [i for i, name in enumerate(normalized) if name in aliases]
        matches += [
            i for i, name in enumerate(normalized)
            if i not in matches and ("municipio" in name or "cidade" in name)
        ]
    else:
        aliases = {
            "territorio", "territorio identidade", "territorio de identidade",
            "nome territorio", "territorio identidade ba",
        }
        matches = [i for i, name in enumerate(normalized) if name in aliases]
        matches += [
            i for i, name in enumerate(normalized)
            if i not in matches and "territorio" in name
        ]
    return matches[0] if matches else None


def load_city_territories(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    content = path.read_bytes()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
    try:
        delimiter = csv.Sniffer().sniff(text[:8192], delimiters=";,	").delimiter
    except csv.Error:
        delimiter = ";"
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not rows:
        return {}
    city_column = _column_index(rows[0], "city")
    territory_column = _column_index(rows[0], "territory")
    if city_column is None or territory_column is None:
        raise IngestFormatError(
            "O CSV de territórios precisa ter colunas de município/cidade "
            "e território de identidade."
        )
    result = {}
    for row in rows[1:]:
        if max(city_column, territory_column) >= len(row):
            continue
        city = row[city_column].strip()
        territory = row[territory_column].strip()
        if city and territory:
            result[normalizar(city)] = territory
    return result
