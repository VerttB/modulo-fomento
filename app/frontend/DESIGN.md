# Design System — Licori (Módulo de Fomento)

Esta camada base aproxima o frontend do Licori do design system do
[`observatorio-front`](https://github.com/observatorio-secti/observatorio-front)
(**Simcc Intelligence**). A referência canônica das regras visuais é o `DESIGN.md`
daquele repositório; aqui fica só o que já foi aplicado e o que falta.

## Onde os tokens vivem

| Arquivo | Papel |
| --- | --- |
| `src/styles/tokens.css` | Fonte da verdade: primitivos, semânticos, tipografia, forma, elevação e aliases legados. |
| `tailwind.config.js` | Espelho dos tokens em nomes de utilitários (`bg-brand`, `text-muted`, `rounded-panel`, `shadow-surface`...). |
| `index.html` | Carrega **Lexend** (texto) e **Ubuntu** (dados tabulares) via Google Fonts. |
| `src/style.css` | Importa os tokens e aplica o tema ao `:root`. |

## Paleta aplicada

| Token | Valor | Uso |
| --- | --- | --- |
| `--color-app` | `#f2f6fb` | Fundo do canvas (nível 0) — tom do protótipo |
| `--color-surface` | `#ffffff` | Cards, painéis, sidebar, topbar (nível 1) |
| `--color-brand` | `#044b8d` | Ações primárias, links, foco — azul da marca do Governo da Bahia |
| `--color-brand-dark` | `#172b43` | Hover de ações primárias, cabeçalhos institucionais — navy do protótipo |
| `--color-brand-container` | `#4a7cb0` | Destaques de apoio |
| `--color-brand-soft` | `#b8d8f0` | Fundos suaves, chips |
| `--color-steel` | `#719cb8` | Borda de accent em cards de perfil |
| `--color-ink` | `#191c1e` | Texto principal |
| `--color-ink-soft` | `#3f484c` | Texto secundário |
| `--color-muted` | `#5b6469` | Labels e metadados (contraste ≥ 4.5:1) |
| `--color-muted-soft` | `#687176` | Texto auxiliar (contraste ≥ 4.5:1) |
| `--color-border` | `#e5e7eb` | Contornos de 1px |
| `--color-danger` | `#b3261e` | Erros (`--color-danger-soft` para fundo) |

Cores de estado (`success`, `warning`, `info`) foram derivadas da mesma escala,
já que o `DESIGN.md` só define explicitamente o `error`.

## Fita do Governo da Bahia

As cores institutionais saíram da própria marca em `public/marca/governo-bahia-secti.png`
(amostragem pixel a pixel do PNG):

| Cor da fita | Hex | Papel no Licuri |
| --- | --- | --- |
| Azul | `#044b8d` | `--color-brand`, série 1 do gráfico, territórios do mapa |
| Ciano | `#29b3b6` | Lavagens e ícones |
| Verde | `#93c025` | Lavagens e ícones |
| Amarelo | `#f8b818` | Faixa decorativa do banner |
| Laranja | `#ee800d` | Lavagens e ícones |
| Magenta | `#e10e7f` | Lavagens e ícones |
| Vermelho | `#e00e1b` | Faixa decorativa do banner |

As cores vivas ficam abaixo de 3:1 sobre branco, então **não** são usadas em
texto nem em marcas de dados. Cada matiz tem duas variantes:

- `*-ink` (mesma matiz escurecida): texto e ícones — entre 5,3:1 e 8,8:1.
- `*-data` (tom médio): barras, linhas e áreas do mapa — entre 3,3:1 e 6:1.

As séries de dados usam `--chart-1` … `--chart-7`, na ordem azul, ciano, verde,
âmbar, laranja, magenta, vermelho. O mapa de territórios usa a mesma fita em
27 tons (cada ciclo um pouco mais escuro), todos ≥ 3:1 contra o fundo do mapa.

## Tipografia

- **Lexend** como família padrão e de display (`--font-sans`, `--font-display`).
- **Ubuntu** para números e séries (`--font-data`, `text-data`).
- Escala: `label-sm` 12 · `caption` 12 · `body` 14 · `body-lg` 16 · `title` 18 · `heading` 24 · `display` 36.
- Não há mais texto em 11px: `--text-label-sm` e `--text-brand-description` foram para 12px e os `font-size: 11px` fixos acompanharam.

## Forma, espaçamento e elevação

- Controles (botões, inputs): `--radius-control` = **8px**.
- Painéis e cards: `--radius-panel` = **8px** (o protótipo usa 5px; 8px mantém a mesma família dos controles).
- Badges e chips: `--radius-pill`.
- Base de espaçamento 4px; gutter 24px; margem externa desktop 64px; container 1280px.
- Superfícies planas (cards de métrica, painéis, barra de filtros e busca) usam **borda de 1px e nenhuma sombra**, como no protótipo do Observatório. `--shadow-surface` fica definido apenas como referência e não é mais aplicado.
- `--shadow-overlay` (menus e modais) continua em uso.

## Migração da paleta (feita)

Os estilos deixaram de usar hex fixos. O que foi convertido:

| Arquivo | O que mudou |
| --- | --- |
| `src/styles/app.css` | Shell, sidebar, topbar, banner, cards de métrica, painéis, tabelas, Maria |
| `src/styles/api.css` | Badges, estados, avisos e tabelas |
| `src/styles/utilities.css` | Filtros e menus |
| `src/componentes/mapa/MapaCidades.css` | Mapa, legenda e cartões de seleção |
| `src/componentes/graficos/TrendChart.jsx` | Série do gráfico em `--chart-1` (azul da Bahia) |
| `src/componentes/mapa/MapaCidades.jsx` | Paleta categórica dos 27 territórios na fita do Bahia |

Hex restantes no projeto, de propósito:

- `src/styles/tokens.css` — é a definição dos tokens.
- `TrendChart.jsx` e `MapaCidades.jsx` — cores aplicadas como atributo SVG/Leaflet, onde `var()` não resolve; os valores espelham os tokens.
- Dois `#fff` dentro de `color-mix()` em `app.css` e `api.css`.

## Item 1 aplicado — contraste, forma, tipografia e ícones

| Frente | O que foi feito |
| --- | --- |
| Contraste | `--color-muted` (#5b6469) e `--color-muted-soft` (#687176) substituem #6f787d/#98a1a6. Contraste ≥ 4.5:1 sobre branco, `--color-app` e `--color-surface-low`. |
| Raios | 43 valores fixos trocados por `--radius-control` (8px) ou `--radius-panel` (8px). Chips e badges usam `--radius-pill`. |
| Tipografia | 157 declarações normalizadas para a escala 11/12/14/16/18/20/24. O `h1` já seguia 24px/20px. |
| Ícones | `lucide-react` substitui os glifos Unicode na navegação, cards de métrica, filtros, paginação, exportação, mapa e perfil de instituição. `aria-hidden="true"` nos decorativos. |
| Layout dos filtros | Cada filtro virou um controle visível: borda, fundo cinza-claro, raio de 8px, chevron e cursor de ponteiro. Hover e estado aberto usam o azul da marca; seleções ativas ficam destacadas. Abaixo de 1250px o painel vira grade de 4 colunas (3 em ≤980px, 2 em ≤700px). O menu fechado do multi-select usa `display:none` para não gerar scroll horizontal. |

## Item 4 aplicado — acessibilidade da navegação

| Frente | O que foi feito |
| --- | --- |
| Skip link | `Pular para o conteúdo` é o primeiro elemento focável; leva ao `<main id="conteudo" tabindex="-1">` e só aparece no foco. |
| Item atual | O item ativo da navegação recebe `aria-current="page"`, inclusive o atalho de Instituições no perfil e o subitem Ingestões. |
| Botão do menu | `aria-expanded`, `aria-controls="menu-principal"` e `aria-label` alternando entre **Abrir menu** e **Fechar menu**. |
| Sidebar mobile | Overlay para fechar ao clicar fora, fecha com **ESC**, foco preso na sidebar enquanto aberta e devolvido ao botão ao fechar. Fora da tela, a sidebar usa `visibility: hidden` para sair da ordem de tabulação. |

## Alinhamento ao protótipo (Pacote A)

Divergências de design absorvidas do protótipo do orientador. As divergências de
arquitetura de informação (Maria como porta de entrada) e a seção Produção/Qualis
ficaram de fora: a última depende de dados e rota que não existem no backend.

| Frente | O que foi feito |
| --- | --- |
| Superfícies | Removida a sombra de `.metric-card`, `.panel`, `.filterbar` e `.search-toolbar`. Ficam só borda de 1px sobre o fundo claro, como nos cards do protótipo. |
| Microtipografia | 68 declarações `font-size: 11px` passaram para 12px, mais o avatar da topbar. O menor texto do app deixa de ser 11px. |
| Título | `h1` de 24px para 28px (22px no mobile), com margem do cabeçalho de 21px para 26px. |
| Gráfico de linha | Área dos rótulos do eixo Y de 29px para 34px, para os valores de 12px não encostarem na série. |
| Tom narrativo | `src/core/viewMeta.js` guarda um subtítulo por seção ("Uma trajetória de apoio à formação científica na Bahia."). O `h1` continua sendo o nome da seção, alinhado ao menu e ao breadcrumb. |
| Selo de recorte | `.record-scope` mostra "Recorte atual · N registros" e quantos filtros estão ativos, logo abaixo do cabeçalho, nas telas de relatório. |
| Notas de leitura | `ReadingNote` renderiza uma linha explicativa abaixo do gráfico (`.reading-note`), com ícone de informação e fio superior. Aplicado à evolução do fomento, às modalidades e aos indicadores. |
| Raios | `--radius-panel` de 12px para 8px: painéis, banner, barra de filtros e containers da Maria. |
| Paleta | `--color-app` de `#f8f9fb` para `#f2f6fb` e navy de `#024a60` para `#172b43`, os tons do protótipo. |
| Marcas | Logo colorida do Governo da Bahia / SECTI no rodapé da sidebar, acima da FAPESB, servida de `public/marca/governo-bahia-secti.png` (1600×622). |

## Fita do Governo da Bahia aplicada

A identidade visual passa a usar as cores da marca do governo, extraídas do
próprio arquivo da logo:

| Frente | O que foi feito |
| --- | --- |
| Marca principal | `--color-brand` de `#07677e` para `#044b8d` (azul da fita). Links, botões, foco, eyebrow e bordas ativas seguem essa cor. |
| Séries de dados | `--chart-1` … `--chart-7` percorrem a fita (azul, ciano, verde, âmbar, laranja, magenta, vermelho) em tons com ≥ 3:1 no branco. Cada painel de barras tem um tom próprio. |
| Gráfico de linha | A evolução do fomento e a taxa de população usam `--chart-1` e `--chart-3`, com gradiente de área em `var(--chart-1)`. |
| Mapas | Os 27 territórios passam da família azul para a fita, cada ciclo mais escuro. Legenda acompanha a mesma escala. |
| Banner | Faixa decorativa de 4px com as 7 cores da fita no rodapé do banner; o núcleo "BA" virou gradiente azul do estado. |
| Texto e ícones | Cores vivas da fita não passam de 2,7:1 no branco: texto e ícones usam as variantes `*-ink` (5,3:1 a 8,8:1) e as lavagens `*-wash` nos chips. |
| Estados | `success` virou o verde da fita (`#557512`), `warning` o âmbar (`#8a5a10`), `danger` o vermelho (`#b3261e`) e `info` o ciano (`#0b6f73`). |

## Leitura e marca (fita, animação, logos e impressão)

| Frente | O que foi feito |
| --- | --- |
| Fita no app | A faixa da fita do Bahia aparece em três lugares fixos: 3px no rodapé da topbar (todas as telas), 4px sob a marca Licuri na sidebar e 2px no topo do rodapé de cada página. Os cards de métrica ganharam um acento de 3px no topo, um tom por card. |
| Desenho do banner | As três órbitas giram em velocidades diferentes (26s, 34s, 42s), o núcleo "BA" pulsa e brilha, e as estrelas cintilam. Tudo em `src/styles/bahia.css`, com `prefers-reduced-motion` desligando as animações. |
| Leitura do mapa | O container do Leaflet vira `role="region"` com `aria-label` e `aria-describedby`, ganha `tabindex` e navegação por setas (`keyboard`). Abaixo do mapa há um resumo em texto (territórios, municípios, população, registros e território com mais registros) e o link "Ver em tabela", que leva aos painéis de lista. |
| Gráfico de linha | "Ver os dados em tabela" abre a série completa (ano × registros) em tabela real, com `caption` e `scope`. |
| Logos das instituições | 11 logos do Observatório (`observatorio-front/public/university-logo`) foram convertidos para WebP, com no máximo 400px, e entraram em `public/instituicoes/`. A sigla é casada por token, então "IHAC - UFBA" encontra o logo da UFBA. Instituições fora do catálogo continuam com as iniciais. |
| Peso das imagens | Os logos foram de 6,5 MB para 115 KB; a marca do Governo, de 232 KB para 3,8 KB em WebP (o PNG segue como fallback em `<picture>`). |
| Impressão | `src/styles/print.css` esconde menu, filtros, busca e botões, mantém gráficos e tabelas, e evita que um painel quebre entre páginas. |

## Pendências conhecidas

- **Mapa multicolorido**: a fita deixa o mapa mais legível por território, mas mais saturado que o protótipo. Se o orientador preferir, dá para reduzir a escala para azul/ciano/verde.
- **Ícones restantes**: verificados apenas os pontos com glifos Unicode; novos componentes devem importar de `lucide-react` em vez de usar símbolos.
- **`por_subarea` vazio na API pública**: o painel "Bolsistas por subárea" fica em estado vazio nos dados de produção; não é falha do frontend.
- **Cobertura dos logos**: só 11 instituições do catálogo têm logo; as outras 49 continuam com as iniciais.
- **Contagem de territórios**: o GeoJSON tem 26 territórios, não 27 — o contador do mapa agora usa o dado real.
