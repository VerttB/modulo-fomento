import argparse
import json
from pathlib import Path
from uuid import UUID

from src.core.database import SessionLocal
from src.services.ingestao import travar_ingestao
from src.services.recuperacao_cidades import recuperar_cidades
from src.services.recuperacao_localizacao import recuperar_ceps


def main():
    parser = argparse.ArgumentParser(description="Recupera CEPs de bolsas a partir de arquivo verificado.")
    parser.add_argument("--ingestao", required=True, type=UUID)
    parser.add_argument("--arquivo", required=True, type=Path)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db, travar_ingestao(db.get_bind(), args.ingestao):
        result, alternativas = recuperar_ceps(db, args.ingestao, args.arquivo, args.aplicar)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.aplicar:
            result = recuperar_cidades(db, alternativas)
            print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
