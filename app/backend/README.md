# API — Módulo de Fomento

Serviço FastAPI versionado sob `/api/v1`. Consulte o README da raiz para instruções do monorepo, configuração, migrações e execução.

## Atualizar nomes de pesquisadores pela ODA

A atualização é um comando operacional, não uma rota HTTP. Configure `ODA_PESQUISADORES_URL` e execute na raiz do monorepo:

```sh
docker compose run --rm --no-deps api /app/.venv/bin/python -m src.commands.atualizar_pesquisadores_oda
```

O comando percorre automaticamente os pesquisadores pendentes em lotes de até 100, registra progresso no terminal e salva o ponto de retomada em `INGESTOES_PATH/atualizacao_pesquisadores_oda.checkpoint.json`. Ao concluir, remove o checkpoint. Se houver falha, execute o mesmo comando para retomar; use `--reiniciar` para ignorar o checkpoint e recomeçar. O tamanho do lote pode ser alterado com `--tamanho-lote 50`.
