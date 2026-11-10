import argparse
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from src.core.config import settings
from src.core.database import SessionLocal
from src.schemas.atualizacao_pesquisadores import AtualizacaoPesquisadoresResultado
from src.services.atualizacao_pesquisadores import atualizar_pendentes


TAMANHO_LOTE_PADRAO = 100
TAMANHO_LOTE_MAXIMO = 100
NOME_CHECKPOINT = "atualizacao_pesquisadores_simcc.checkpoint.json"


def _ler_checkpoint(caminho: Path) -> UUID | None:
    if not caminho.exists():
        return None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        valor = dados.get("ultimo_id")
        return UUID(valor) if valor else None
    except (OSError, ValueError, AttributeError) as erro:
        raise ValueError(f"Checkpoint inválido em {caminho}; use --reiniciar para começar do início.") from erro


def _salvar_checkpoint(caminho: Path, ultimo_id: UUID) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(f"{caminho.name}.tmp")
    temporario.write_text(
        json.dumps({"ultimo_id": str(ultimo_id)}, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(temporario, caminho)


def _resumo_lote(resultado: AtualizacaoPesquisadoresResultado) -> dict:
    return resultado.model_dump(mode="json")


def executar(
    tamanho_lote: int,
    checkpoint: Path,
    apos_id: UUID | None = None,
    reiniciar: bool = False,
) -> int:
    if apos_id is not None and reiniciar:
        print("Use --apos-id ou --reiniciar, não ambos.", file=sys.stderr)
        return 2

    try:
        cursor = apos_id if apos_id is not None else (None if reiniciar else _ler_checkpoint(checkpoint))
    except ValueError as erro:
        print(str(erro), file=sys.stderr)
        return 2

    totais = {
        "consultados": 0,
        "atualizados": 0,
        "fotos_atualizadas": 0,
        "sem_resultado": 0,
        "alterados_concorrentemente": 0,
    }
    lote_numero = 0

    with SessionLocal() as db:
        while True:
            lote_numero += 1

            def salvar_progresso(ultimo_id: UUID, andamento: AtualizacaoPesquisadoresResultado) -> None:
                _salvar_checkpoint(checkpoint, ultimo_id)
                if andamento.consultados % 10 == 0:
                    print(json.dumps({
                        "lote": lote_numero,
                        "consultados_no_lote": andamento.consultados,
                        "atualizados_no_lote": andamento.atualizados,
                        "fotos_atualizadas_no_lote": andamento.fotos_atualizadas,
                        "sem_resultado_no_lote": andamento.sem_resultado,
                        "ultimo_id": str(ultimo_id),
                    }, ensure_ascii=False), flush=True)

            resultado = atualizar_pendentes(db, tamanho_lote, cursor, salvar_progresso)
            cursor = resultado.ultimo_id
            if cursor is not None:
                _salvar_checkpoint(checkpoint, cursor)

            for campo in totais:
                totais[campo] += getattr(resultado, campo)

            print(json.dumps({"lote": lote_numero, **_resumo_lote(resultado)}, ensure_ascii=False), flush=True)

            if resultado.erro:
                print("Execução interrompida; o checkpoint foi preservado para retomada.", file=sys.stderr)
                return 1

            if resultado.concluido:
                checkpoint.unlink(missing_ok=True)
                print(json.dumps({"total": totais, "concluido": True}, ensure_ascii=False), flush=True)
                return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atualiza em sequência os nomes dos pesquisadores pendentes pela API SIMCC."
    )
    parser.add_argument(
        "--tamanho-lote",
        type=int,
        default=TAMANHO_LOTE_PADRAO,
        choices=range(1, TAMANHO_LOTE_MAXIMO + 1),
        metavar=f"1-{TAMANHO_LOTE_MAXIMO}",
    )
    parser.add_argument("--apos-id", type=UUID, help="Retoma após este UUID, ignorando o checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=settings.ingestoes_path / NOME_CHECKPOINT)
    parser.add_argument("--reiniciar", action="store_true", help="Ignora o checkpoint e começa pelo menor ID.")
    args = parser.parse_args()
    raise SystemExit(executar(args.tamanho_lote, args.checkpoint, args.apos_id, args.reiniciar))


if __name__ == "__main__":
    main()
