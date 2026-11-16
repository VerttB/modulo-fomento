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
| `--color-app` | `#f8f9fb` | Fundo do canvas (nível 0) |
| `--color-surface` | `#ffffff` | Cards, painéis, sidebar, topbar (nível 1) |
| `--color-brand` | `#07677e` | Ações primárias, links, foco |
| `--color-brand-dark` | `#024a60` | Hover de ações primárias, cabeçalhos institucionais |
| `--color-brand-container` | `#559fb8` | Destaques de apoio |
| `--color-brand-soft` | `#b6eaff` | Fundos suaves, chips |
| `--color-steel` | `#719cb8` | Borda de accent em cards de perfil |
| `--color-ink` | `#191c1e` | Texto principal |
| `--color-ink-soft` | `#3f484c` | Texto secundário |
| `--color-muted` | `#5b6469` | Labels e metadados (contraste ≥ 4.5:1) |
| `--color-muted-soft` | `#687176` | Texto auxiliar (contraste ≥ 4.5:1) |
| `--color-border` | `#e5e7eb` | Contornos de 1px |
| `--color-danger` | `#ba1a1a` | Erros (`--color-danger-soft` para fundo) |

Cores de estado (`success`, `warning`, `info`) foram derivadas da mesma escala,
já que o `DESIGN.md` só define explicitamente o `error`.

## Tipografia

- **Lexend** como família padrão e de display (`--font-sans`, `--font-display`).
- **Ubuntu** para números e séries (`--font-data`, `text-data`).
- Escala: `label-sm` 11 · `caption` 12 · `body` 14 · `body-lg` 16 · `title` 18 · `heading` 24 · `display` 36.

## Forma, espaçamento e elevação

- Controles (botões, inputs): `--radius-control` = **8px**.
- Painéis e cards: `--radius-panel` = **12px**.
- Badges e chips: `--radius-pill`.
- Base de espaçamento 4px; gutter 24px; margem externa desktop 64px; container 1280px.
- Sombras: `--shadow-surface` (nível 2, difusa e discreta) e `--shadow-overlay` (nível 3, menus e modais).

## Migração da paleta (feita)

Os estilos deixaram de usar hex fixos. O que foi convertido:

| Arquivo | O que mudou |
| --- | --- |
| `src/styles/app.css` | Shell, sidebar, topbar, banner, cards de métrica, painéis, tabelas, Maria |
| `src/styles/api.css` | Badges, estados, avisos e tabelas |
| `src/styles/utilities.css` | Filtros e menus |
| `src/componentes/mapa/MapaCidades.css` | Mapa, legenda e cartões de seleção |
| `src/componentes/graficos/TrendChart.jsx` | Série do gráfico em `#07677e` (`--color-brand`) |
| `src/componentes/mapa/MapaCidades.jsx` | Paleta categórica dos 27 territórios em tons frios |

Hex restantes no projeto, de propósito:

- `src/styles/tokens.css` — é a definição dos tokens.
- `TrendChart.jsx` e `MapaCidades.jsx` — cores aplicadas como atributo SVG/Leaflet, onde `var()` não resolve; os valores espelham os tokens.
- Dois `#fff` dentro de `color-mix()` em `app.css` e `api.css`.

## Item 1 aplicado — contraste, forma, tipografia e ícones

| Frente | O que foi feito |
| --- | --- |
| Contraste | `--color-muted` (#5b6469) e `--color-muted-soft` (#687176) substituem #6f787d/#98a1a6. Contraste ≥ 4.5:1 sobre branco, `--color-app` e `--color-surface-low`. |
| Raios | 43 valores fixos trocados por `--radius-control` (8px) ou `--radius-panel` (12px). Chips e badges usam `--radius-pill`. |
| Tipografia | 157 declarações normalizadas para a escala 11/12/14/16/18/20/24. O `h1` já seguia 24px/20px. |
| Ícones | `lucide-react` substitui os glifos Unicode na navegação, cards de métrica, filtros, paginação, exportação, mapa e perfil de instituição. `aria-hidden="true"` nos decorativos. |
| Layout dos filtros | `.filterbar` passa a usar `flex-wrap: wrap` abaixo de 1250px; o menu fechado do multi-select ganhou `display:none`. Sem isso havia scroll horizontal entre 981px e 1250px. |

## Item 4 aplicado — acessibilidade da navegação

| Frente | O que foi feito |
| --- | --- |
| Skip link | `Pular para o conteúdo` é o primeiro elemento focável; leva ao `<main id="conteudo" tabindex="-1">` e só aparece no foco. |
| Item atual | O item ativo da navegação recebe `aria-current="page"`, inclusive o atalho de Instituições no perfil e o subitem Ingestões. |
| Botão do menu | `aria-expanded`, `aria-controls="menu-principal"` e `aria-label` alternando entre **Abrir menu** e **Fechar menu**. |
| Sidebar mobile | Overlay para fechar ao clicar fora, fecha com **ESC**, foco preso na sidebar enquanto aberta e devolvido ao botão ao fechar. Fora da tela, a sidebar usa `visibility: hidden` para sair da ordem de tabulação. |

## Pendências conhecidas

- **Paleta do mapa**: os 27 territórios agora usam uma família azul; se a leitura ficar difícil, vale revisar a escala.
- **Ícones restantes**: verificados apenas os pontos com glifos Unicode; novos componentes devem importar de `lucide-react` em vez de usar símbolos.
