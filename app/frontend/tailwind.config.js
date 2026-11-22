const token = (name) => `var(--${name})`;

/**
 * Espelho Tailwind dos tokens de src/styles/tokens.css.
 * Os valores canônicos ficam no CSS; aqui só expomos nomes semânticos
 * alinhados ao design system do Observatório ("Simcc Intelligence").
 */
export default {
  theme: {
    extend: {
      colors: {
        app: token("color-app"),
        ink: token("color-ink"),
        "ink-soft": token("color-ink-soft"),
        brand: token("color-brand"),
        "brand-dark": token("color-brand-dark"),
        "brand-container": token("color-brand-container"),
        "brand-soft": token("color-brand-soft"),
        "brand-wash": token("color-brand-wash"),
        "brand-wash-strong": token("color-brand-wash-strong"),
        surface: token("color-surface"),
        "surface-low": token("color-surface-low"),
        "surface-container": token("color-surface-container"),
        border: token("color-border"),
        outline: token("color-outline"),
        muted: token("color-muted"),
        "muted-soft": token("color-muted-soft"),
        steel: token("color-steel"),
        navy: token("color-navy"),
        success: token("color-success"),
        "success-soft": token("color-success-soft"),
        warning: token("color-warning"),
        "warning-soft": token("color-warning-soft"),
        danger: token("color-danger"),
        "danger-soft": token("color-danger-soft"),
        info: token("color-info"),
        "info-soft": token("color-info-soft"),
        /* Fita do Governo da Bahia */
        "chart-1": token("chart-1"),
        "chart-2": token("chart-2"),
        "chart-3": token("chart-3"),
        "chart-4": token("chart-4"),
        "chart-5": token("chart-5"),
        "chart-6": token("chart-6"),
        "chart-7": token("chart-7"),
        "bahia-blue": token("bahia-blue"),
        "bahia-cyan": token("bahia-cyan"),
        "bahia-green": token("bahia-green"),
        "bahia-yellow": token("bahia-yellow"),
        "bahia-orange": token("bahia-orange"),
        "bahia-magenta": token("bahia-magenta"),
        "bahia-red": token("bahia-red"),
      },
      fontFamily: {
        sans: token("font-sans"),
        display: token("font-display"),
        data: token("font-data"),
      },
      fontSize: {
        caption: token("text-caption"),
        body: token("text-body"),
        "body-lg": token("text-body-lg"),
        title: token("text-title"),
        heading: token("text-heading"),
        display: token("text-display"),
        data: token("text-data"),
      },
      borderRadius: {
        control: token("radius-control"),
        panel: token("radius-panel"),
        pill: token("radius-pill"),
      },
      spacing: {
        page: token("spacing-page"),
        "page-inline": token("spacing-page-inline"),
        section: token("spacing-section"),
        gutter: token("spacing-gutter"),
      },
      maxWidth: {
        container: token("width-container"),
      },
      boxShadow: {
        surface: token("shadow-surface"),
        overlay: token("shadow-overlay"),
        focus: token("shadow-focus"),
      },
      backgroundImage: {
        highlight: `linear-gradient(to right, ${token("simcc-highlight-from")}, ${token("simcc-highlight-to")})`,
      },
    },
  },
};
