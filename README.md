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

Para o assistente Maria, configure `MARIA_API_URL` com a URL absoluta da API e `MARIA_API_TIMEOUT_SECONDS` com o tempo máximo de espera em segundos (por exemplo, 120) no ambiente do backend e no `.env` da raiz ao usar Docker. A API do observatório encaminha as solicitações à Maria. As conversas retornadas são compartilhadas pela API externa; não há separação por usuário neste projeto. Os filtros do observatório não são enviados automaticamente às perguntas.

### Recuperação de localização de pesquisadores

O comando `python -m src.commands.recuperar_localizacao --ingestao ID --arquivo CAMINHO` faz uma prévia sem gravar. O arquivo deve ser o original da ingestão e ter o mesmo SHA-256 registrado no banco. Para aplicar, acrescente `--aplicar`. Em Docker, monte o arquivo original como somente leitura em um container temporário e passe o caminho dentro do container. O arquivo pode conter CPF e deve permanecer restrito; o comando não o registra nem o grava no banco.

Exemplo no PowerShell, a partir da raiz do projeto (substitua o caminho e o identificador):

```powershell
docker compose run --rm --no-deps --volume "C:/caminho/arquivo.xlsx:/arquivo/original.xlsx:ro" api /app/.venv/bin/python -m src.commands.recuperar_localizacao --ingestao ID_DA_INGESTAO --arquivo /arquivo/original.xlsx
```

Revise os totais da prévia e repita o comando com `--aplicar` para gravar. É necessário que o serviço de banco esteja acessível e que a API consiga acessar o ViaCEP e o CSV de territórios configurado.

O comando confere os vínculos da bolsa com a linha de rastreabilidade e compara título, data inicial e instituição antes de preencher CEPs ausentes. A ordem é unidade, departamento e instituição. Bolsas com dados divergentes, sem linha confiável ou sem CEP válido são contabilizadas e ignoradas. Depois consulta o ViaCEP por CEP distinto; quando ele confirma que o primeiro CEP da linha não existe, testa o próximo da ordem e registra o primeiro encontrado. Uma falha de comunicação não é tratada como CEP inexistente. A cidade e o território dos pesquisadores são atualizados conforme a última bolsa não descartada, e os indicadores são recalculados. Ao final, confira os contadores e se `metricas_atualizadas` é `1`. Consultas sem resultado não sobrescrevem cidades existentes. Falhas consecutivas interrompem as consultas; o comando pode ser executado novamente com o mesmo arquivo para retomar. Execute uma ingestão por vez e mantenha o arquivo original protegido.

### Atualização provisória de pesquisadores pela ODA

Para habilitar a operação administrativa temporária, configure `ODA_PESQUISADORES_URL=https://oda.vertb.com.br/pesquisadores` e uma chave longa e aleatória em `ODA_ATUALIZACAO_TOKEN`. A rota `POST /api/v1/administracao/pesquisadores/atualizar-oda` recebe a chave no header `X-Atualizacao-Token` e um JSON com `tamanho_lote` (1 a 100, padrão 30) e `apos_id` (opcional). Sem essas configurações, a rota fica desabilitada.

A operação consulta pesquisadores pendentes que já têm Lattes e nome vazio; cada nome encontrado é gravado individualmente e o pesquisador passa a aprovado. Não modifica cidade, território ou pesquisadores rejeitados. A resposta informa quantos foram consultados, atualizados, não encontrados ou alterados em paralelo, além de `ultimo_id`, `concluido` e eventual `erro`. Para continuar, envie o `ultimo_id` da resposta como `apos_id` na próxima chamada até `concluido` ser verdadeiro. Em caso de falha externa, retome usando o mesmo `ultimo_id`; se ele for nulo, reinicie sem `apos_id`. Resultados sem correspondência são contabilizados e só serão consultados novamente ao iniciar uma nova varredura. Se a resposta for perdida, reiniciar a varredura não sobrescreve os nomes já preenchidos. Após o uso, remova as duas configurações e reinicie a API para desabilitar a rota.

## Migrações e testes

As migrations não são aplicadas automaticamente pelo compose. Quando estiver pronto, rode a partir de `app/backend`: `uv run alembic upgrade head`. Para os testes, rode `uv run pytest` no mesmo diretório.

## Dados da interface

O painel, filtros, gráficos, tabelas e exportação CSV consultam a API v1; não há conjunto demonstrativo local nem fallback com números fictícios. Os filtros do relatório usam os agregados da view materializada `mv_bolsas_metricas`; atualize-a após alterações diretas no banco com `uv run python -m src.commands.refresh_bolsas_metrics`. Pesquisadores e projetos são carregados de forma paginada. A tela “Consulta guiada” resume somente os agregados recebidos e não é um assistente de IA generativa.

## Ingestão

`POST /api/v1/ingest` recebe CSV, XLS, XLSX ou ODS no campo multipart `arquivo`, armazena o original e retorna HTTP 202 com o identificador. O Hop processa a fila em segundo plano; a situação e as linhas podem ser acompanhadas na página de ingestões. A situação PROCESSANDO inclui arquivos na fila e execuções em andamento. A leitura distingue as duas colunas “Data Final”: a primeira representa a saída do pesquisador e a segunda o fim da bolsa. CPF, quando presente no arquivo, serve apenas para consultar os serviços externos e não é armazenado no banco.

## Apache Hop — prova de conceito

Configure `HOP_INGEST_API_URL=http://api:8000` no `.env` da raiz. O serviço leve `hop-dispatcher` recebe notificações do PostgreSQL e inicia um container Hop temporário para cada ingestão, sem consultas periódicas à fila durante a espera. A fila permanece no banco e é verificada novamente quando o disparador inicia ou reconecta. Falhas ao iniciar o Hop provocam uma nova tentativa após um intervalo; falhas registradas pela ingestão permanecem para análise. Após interrupção, a retomada usa os lotes confirmados e o bloqueio da ingestão. As regras e a rastreabilidade continuam no backend.

O serviço `hop-image` garante que a imagem do Hop esteja disponível e termina imediatamente. Os containers de execução são removidos após terminar; acompanhe as mensagens de coordenação com `docker compose logs -f hop-dispatcher` e a execução pela página de ingestões. Como o disparador monta `/var/run/docker.sock`, ele tem acesso amplo ao Docker do host; mantenha esse serviço restrito a um ambiente confiável.

Configure `HOP_INGEST_API_URL` com o endereço da API acessível pelo container (por exemplo, `http://api:8000`) e `HOP_INGESTAO_ID` com o UUID de uma ingestão que pode ser retomada. Com a API disponível, execute:

```sh
docker compose --profile hop run --rm hop
```

O workflow não recebe nem armazena o arquivo original ou CPFs. Falhas HTTP produzem uma execução com erro; consulte os detalhes e as tentativas na página de ingestões. Uma falha de comunicação não confirma se a API concluiu a operação: consulte o estado da ingestão antes de executá-la novamente.
