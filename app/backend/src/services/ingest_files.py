import csv
import hashlib
import io
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from src.core.config import settings
from src.core.exceptions import IngestFormatError
from src.services.ingest_reader import normalizar_cpf, texto_linha


CHUNK_BYTES = 1024 * 1024


def nome_arquivo_seguro(filename: str) -> str:
    return Path(filename.replace("\\", "/")).name or "arquivo-sem-nome"


def caminho_lote(ingestao_id: UUID) -> Path:
    return settings.ingestoes_path / str(ingestao_id)


def caminho_seguro(relative_path: str) -> Path:
    root = settings.ingestoes_path.resolve()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Caminho do arquivo da ingestão inválido.")
    return path


def salvar_upload(ingestao_id: UUID, filename: str, source: BinaryIO) -> tuple[str, str]:
    folder = caminho_lote(ingestao_id)
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(nome_arquivo_seguro(filename)).suffix.casefold()
    original = folder / f"original{suffix}"
    temporary = folder / f".original{suffix}.uploading"
    digest = hashlib.sha256()
    try:
        with temporary.open("wb") as target:
            while chunk := source.read(CHUNK_BYTES):
                digest.update(chunk)
                target.write(chunk)
        temporary.replace(original)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return str(original.relative_to(settings.ingestoes_path)), digest.hexdigest()


def salvar_conteudo_upload(ingestao_id: UUID, filename: str, content: bytes) -> tuple[str, str]:
    return salvar_upload(ingestao_id, filename, io.BytesIO(content))


def salvar_versao_com_lattes(
    ingestao_id: UUID,
    filename: str,
    rows: list[list[object]],
    indices: dict[str, int],
    identificacoes: dict[str, tuple[str | None, str | None, str | None, str | None]],
) -> str:
    cpf_index = indices["cpf_pesquisador"]
    folder = caminho_lote(ingestao_id)
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / "arquivo_com_lattes.csv"
    temporary = output.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        for row_number, source_row in enumerate(rows, start=1):
            row = list(source_row)
            if row_number == 1:
                row[cpf_index] = "Lattes Pesquisador"
            elif cpf_index < len(row):
                cpf_value = texto_linha(row, indices, "cpf_pesquisador")
                lattes = None
                if cpf_value:
                    try:
                        cpf = normalizar_cpf(cpf_value)
                        lattes = identificacoes.get(cpf, (None, None, None, None))[0]
                    except IngestFormatError:
                        pass
                row[cpf_index] = lattes or ""
            writer.writerow(row)
    temporary.replace(output)
    return str(output.relative_to(settings.ingestoes_path))


