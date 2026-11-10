# API — Módulo de Fomento

Serviço FastAPI versionado sob `/api/v1`. Consulte o README da raiz para instruções do monorepo, configuração, migrações e execução.

## Atualizar nomes de pesquisadores pelo SIMCC

A atualização é um comando operacional, não uma rota HTTP. O comando consulta o SIMCC com `lattes_id` e `collection=all`; atualiza o nome e registra a URL da foto em uma tabela ligada ao pesquisador. Cidade e território continuam sendo preenchidos pelo fluxo das bolsas e pelo CSV de municípios. Execute na raiz do monorepo:

```sh
docker compose run --rm --no-deps api /app/.venv/bin/python -m src.commands.atualizar_pesquisadores_simcc
```

O comando percorre automaticamente os pesquisadores pendentes em lotes de até 100, registra progresso no terminal e salva o ponto de retomada em `INGESTOES_PATH/atualizacao_pesquisadores_simcc.checkpoint.json`. Ao concluir, remove o checkpoint. Se houver falha, execute o mesmo comando para retomar; use `--reiniciar` para ignorar o checkpoint e recomeçar. O tamanho do lote pode ser alterado com `--tamanho-lote 50`.
