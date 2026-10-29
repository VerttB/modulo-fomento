# Orientações para agentes

Este arquivo se aplica a todo o monorepo. Consulte-o antes de alterar o projeto.
As instruções explícitas do usuário têm precedência sobre estas orientações.
Mantenha este documento atualizado com decisões aprovadas, sem transformá-lo em
um histórico de tarefas. Uma regra registrada aqui não significa que todo o
código existente já esteja em conformidade com ela.

## Regras gerais

- Comunique-se com o usuário em português.
- Antes de editar, apresente o escopo proposto e solicite feedback. Quando o
  usuário já tiver aprovado o escopo, execute-o sem pedir a mesma confirmação
  novamente. Apresente mudanças materiais de escopo antes de implementá-las.
- Quando o pedido for de planejamento, não altere arquivos até receber autorização.
- Preserve alterações existentes e arquivos do usuário. Não remova arquivos
  desconhecidos, backups ou dados como parte de uma limpeza presumida.
- Não crie commits, execute migrations ou limpe dados sem solicitação do usuário.
- Nunca versione credenciais, arquivos `.env`, backups ou arquivos de ingestão
  com dados pessoais. Documente as variáveis necessárias em `.env.example`, sem
  segredos ou valores que ocultem configurações obrigatórias ausentes.
- Divida arquivos de código que ultrapassem 300 linhas por responsabilidade.
  Para fluxos complexos, use casos de uso específicos. Evite fragmentação
  artificial e arquivos que apenas reexportam código sem uma finalidade clara.
- Ao encontrar a mesma lógica repetida mais de três vezes, avalie uma função,
  schema ou constante compartilhada. Preserve arquivos e comportamentos próprios
  de cada entidade; não imponha abstrações genéricas que dificultem alterações
  isoladas de rotas e entidades.
- Ao concluir, informe o que mudou, quais verificações foram realizadas e quais
  limitações permanecem. Não declare verificações que não foram executadas.

## Backend — `app/backend/`

### Organização e responsabilidades

- Use Python com UV para gerenciar dependências e executar comandos do projeto.
- Mantenha a API versionada em `/api/v1`.
- `routes/` recebe e valida parâmetros, chama serviços e devolve respostas HTTP.
  Não coloque consultas ao banco, regras de negócio, transformação de dados ou
  geração de arquivos nas rotas.
- Coloque essas responsabilidades em `services/`. Organize fluxos complexos em
  casos de uso dentro dos serviços, com arquivos específicos por responsabilidade.
- Existem casos de uso em `src/use_cases/v1/`. Sua eventual reorganização deve
  fazer parte de um escopo aprovado; não mova módulos não relacionados à tarefa.
- Use o tratamento centralizado de erros. Serviços sinalizam erros da aplicação;
  rotas não devem repetir blocos de tratamento de exceções.
- Centralize configurações de ambiente em `src/core/config.py`, usando
  `pydantic-settings`. Evite leituras de ambiente espalhadas pelo código e valores
  padrão para configurações obrigatórias ou credenciais.

### Schemas, filtros e dados

- Centralize filtros compartilhados em schemas e mantenha a paginação separada.
- Use `page=1` e `size=30` como padrões de paginação, com validação dos limites.
- Preserve os nomes das entidades e campos conforme o domínio e o banco.
- Filtros múltiplos do mesmo tipo aceitam qualquer valor selecionado; filtros de
  tipos diferentes são combinados para restringir o resultado.
- Crie ou altere os models primeiro. Gere a migration com base nos models e
  revise o resultado, incluindo enums, índices, relacionamentos e constraints.
- Operações não representadas integralmente pelos models, como views
  materializadas e extensões, exigem ajustes explícitos e revisados na migration.
- Gerar uma migration não autoriza executá-la.
- Diferencie quantidade de pesquisadores únicos e quantidade de registros de
  bolsas. Não trate essas métricas como equivalentes.
- Mantenha documentos de referência, como CSVs de municípios, população e
  territórios, em diretório de dados dedicado, separado do código.

### Ingestão e rastreabilidade

- Não persista CPF no banco nem o inclua em logs ou mensagens de erro.
- Use o CPF apenas transitoriamente para identificação. Evite repetir consultas
  externas para o mesmo CPF dentro de uma ingestão.
- Preserve a linha original do arquivo antes de filtros, remoção de duplicatas
  ou divisão em lotes. Nunca derive a linha de origem da posição na lista filtrada.
- Preserve resultados, motivos, conflitos, tentativas e vínculos de rastreabilidade.
- O processamento deve permitir retomada sem duplicar registros já confirmados.
  A persistência do lote e do ponto de retomada deve ser consistente.
- Diferencie falha de comunicação externa de uma resposta sem pesquisador.
- Arquivos originais usados para retomada ficam em armazenamento restrito, fora
  do versionamento. A versão final arquivada deve substituir CPFs por Lattes e
  não conter CPF. Não invente identificadores para consultas sem resultado.

## Frontend — `app/frontend/`

### Organização e comunicação com a API

- Mantenha React em SPA.
- Coloque componentes reutilizáveis em `src/componentes/`. Páginas coordenam a
  interface; componentes têm responsabilidades delimitadas.
- Chamadas ao backend ficam em `src/services/`, separadas por recurso. Componentes
  e páginas consomem esses serviços, sem duplicar chamadas HTTP.
- Mantenha tipagens compartilhadas de entidades e contratos em `src/core/`.
- Use URL absoluta da API configurada por ambiente e documentada em `.env.example`.
- Evite concentrar regras, requisições e controle de downloads em `App.jsx`.
- Preserve filtros múltiplos e seus parâmetros nas consultas e exportações.
- Recursos estáticos, como o JSON de territórios, ficam em diretório apropriado,
  como `public/`, e não misturados aos componentes.

### Interface e estilos

- Centralize cores, bordas, tipografia e espaçamentos no tema Tailwind.
- Use `tailwind.config.js` e `src/style.css` conforme a integração existente;
  mantenha as importações do Tailwind e variáveis de estilo centralizadas.
- Evite valores visuais repetidos que deveriam ser tokens do tema.
- Mostre estados de carregamento, erro e ausência de dados de forma consistente.
  Downloads devem indicar carregamento e impedir acionamentos duplicados.
- Use “bolsistas” na interface, distinguindo explicitamente pessoas únicas de
  registros de bolsas quando apresentar métricas.
- A exportação deve considerar o recorte completo dos filtros ativos, sem ficar
  limitada à página atualmente exibida.

## Verificação

Execute verificações proporcionais à mudança. Alterações apenas documentais não
exigem build ou execução de testes da aplicação.

Comandos disponíveis, executados a partir do diretório indicado:

| Diretório | Comando | Finalidade |
| --- | --- | --- |
| `app/backend/` | `uv run pytest` | Executar testes do backend |
| `app/backend/` | `uv run python -m compileall -q src` | Verificar sintaxe Python; não substitui testes |
| `app/frontend/` | `npm run typecheck` | Verificar tipos |
| `app/frontend/` | `npm run build` | Validar a compilação do frontend |
| Raiz | `git diff --check` | Verificar problemas de whitespace no diff |

- Em mudanças de contratos, valide parâmetros, respostas e integração entre front
  e back. Para filtros, verifique múltiplos valores e sua combinação com paginação
  nas rotas reais, não apenas schemas isolados.
- Para ingestão, valide falhas, retomada, duplicatas, conflitos e linha original.
- Para exportação, valide conteúdo, filtros, formato, headers e sanitização de
  valores que possam ser interpretados como fórmulas em planilhas.
- Não use banco compartilhado ou dados reais em testes destrutivos. Informe
  dependências ausentes ou falhas preexistentes, sem ocultá-las.

## Mudanças planejadas — não representam funcionalidades concluídas

Os itens abaixo registram o planejamento atual. A criação deste documento não
autoriza sua implementação automática.

### Busca

- A busca lógica é exclusiva da rota de projetos. As buscas de bolsistas,
  pesquisadores e instituições mantêm seu comportamento textual simples.
- A busca de projetos usa a configuração textual do PostgreSQL em português,
  removendo acentos e stop words, com `AND`, `OR`, `NOT`, parênteses e frases.
- Sem operador lógico explícito, a expressão digitada deve preservar ordem e
  proximidade, usando consulta de frase. Em expressões lógicas, palavras em
  sequência precisam ser agrupadas com aspas.
- O vetor de busca do projeto combina título (`nome`) e resumo, com pesos distintos,
  em coluna `tsvector` armazenada e indexada com GIN. A inclusão da área requer
  tratamento da atualização da área relacionada.

### Exportação

- Separar exportações em rotas próprias, com preparação dos dados e geração de
  arquivos nos serviços, compartilhando essa preparação entre CSV e XLSX.
- Selecionar o formato pelo header HTTP `Accept` e tratar formatos incompatíveis.
- Definir a transição dos endpoints antigos antes de removê-los.
- Separar também o serviço de exportação e o controle de downloads no frontend.

### Apache Hop

- Avaliar e realizar a migração gradual da execução da ingestão para Apache Hop,
  começando por uma prova de conceito com critérios de aceitação definidos.
- A divisão proposta mantém a coordenação de pipelines no Hop e as regras de
  domínio nos serviços Python, evitando duas implementações da mesma regra.
- Preservar rastreabilidade, CPF transitório, pontos de retomada, processamento em
  lotes e reexecução sem duplicação. A adoção do Hop, sozinha, não garante retomada.
- Versionar o projeto Hop no monorepo e planejar sua configuração por ambiente,
  integração ao Docker e acompanhamento pela interface administrativa.
