const token = (name) => `var(--${name})`;

export default {
  theme: {
    extend: {
      colors: {
        app: token("color-app"),
        ink: token("color-ink"),
        brand: token("color-brand"),
        "brand-dark": token("color-brand-dark"),
        surface: token("color-surface"),
        border: token("color-border"),
        muted: token("color-muted"),
      },
      fontFamily: {
        sans: token("font-sans"),
      },
      fontSize: {
        caption: token("text-caption"),
        body: token("text-body"),
        heading: token("text-heading"),
      },
      borderRadius: {
        control: token("radius-control"),
        panel: token("radius-panel"),
      },
      spacing: {
        page: token("spacing-page"),
        section: token("spacing-section"),
      },
    },
  },
};
