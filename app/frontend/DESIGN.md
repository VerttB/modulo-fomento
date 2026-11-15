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
| `--color-muted` | `#6f787d` | Labels e metadados |
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

## Pendências conhecidas

- **Tamanhos de fonte**: só o `h1` da página foi normalizado (24px desktop / 20px mobile). O resto mantém a escala antiga (27px, 25.9px, 15.3px...), que não é a do `DESIGN.md` (36/24/20/18/16/14/12/11).
- **Raios de canto**: os componentes ainda usam valores fixos (9px, 10px, 13px). O design system pede 8px para controles e 12px para painéis — trocar `border-radius` por `var(--radius-control)` / `var(--radius-panel)` é o próximo ajuste.
- **Paleta do mapa**: os 27 territórios agora usam uma família azul; se a leitura ficar difícil, vale revisar a escala.
