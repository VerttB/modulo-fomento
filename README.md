# Módulo de Fomento — monorepo v1

O repositório reúne a API Python (FastAPI, SQLAlchemy e Alembic) e a SPA React + Vite:

```text
app/
  backend/   API, modelos, casos de uso, testes e migrations
  frontend/  SPA React
data/        arquivos auxiliares da ingestão
docker-compose.yml
```

## Executar com Docker

Copie `.env.example` para `.env`, defina uma senha forte em `POSTGRES_PASSWORD` e confira `VITE_API_BASE_URL` e `CORS_ALLOWED_ORIGINS` para os endereços da interface e da API. Então execute `docker compose up --build` na raiz. A interface ficará em `http://localhost:5173`, a API em `http://localhost:10010` e a documentação em `http://localhost:10010/docs`.

## Executar localmente

Para desenvolvimento local, entre em `app/backend`, copie `.env.example` para `.env`, configure `DATABASE_URL`, instale as dependências com `uv sync --dev` e inicie com `uv run uvicorn src.main:app --reload`. Para a interface, em outro terminal entre em `app/frontend`, instale com `npm install` e execute `npm run dev`.

## Migrações e testes

As migrations não são aplicadas automaticamente pelo compose. Quando estiver pronto, rode a partir de `app/backend`: `uv run alembic upgrade head`. Para os testes, rode `uv run pytest` no mesmo diretório.

## Dados da interface

O painel, filtros, gráficos, tabelas e exportação CSV consultam a API v1; não há conjunto demonstrativo local nem fallback com números fictícios. Os filtros do relatório usam os agregados da view materializada `mv_bolsas_metricas`; atualize-a após alterações diretas no banco com `uv run python -m src.commands.refresh_bolsas_metrics`. Pesquisadores e projetos são carregados de forma paginada. A tela “Consulta guiada” resume somente os agregados recebidos e não é um assistente de IA generativa.

## Ingestão

`POST /api/v1/ingest` recebe CSV, XLS, XLSX ou ODS no campo multipart `arquivo`. A leitura distingue as duas colunas “Data Final”: a primeira representa a saída do pesquisador e a segunda o fim da bolsa. CPF, quando presente no arquivo, serve apenas para consultar os serviços externos e não é armazenado no banco.
