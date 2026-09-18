# Tokens para web (CSS y Tailwind)

Los valores salen de `MASTER.md`; aqui solo la estructura.

## tokens.css

```css
:root {
  /* Color: nombres semanticos, nunca por tono ("azul") */
  --color-primary: #2563EB;
  --color-on-primary: #FFFFFF;
  --color-secondary: #475569;
  --color-accent: #F59E0B;
  --color-bg: #FFFFFF;
  --color-surface: #F8FAFC;
  --color-text: #0F172A;
  --color-text-muted: #475569;
  --color-success: #15803D;
  --color-warning: #B45309;
  --color-error: #B91C1C;
  --color-focus: var(--color-primary);

  /* Tipografia: escala fluida, cuerpo nunca menor a 1rem */
  --font-heading: "Titulos", system-ui, sans-serif;
  --font-body: "Cuerpo", system-ui, sans-serif;
  --text-sm: clamp(0.875rem, 0.85rem + 0.1vw, 0.9375rem);
  --text-body: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1.05rem + 0.4vw, 1.25rem);
  --text-h2: clamp(1.5rem, 1.2rem + 1.2vw, 2rem);
  --text-h1: clamp(2rem, 1.5rem + 2vw, 3rem);
  --leading-body: 1.5;
  --leading-heading: 1.15;

  /* Espaciado: exactamente la escala de MASTER.md */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px; --space-16: 64px;

  /* Radio y motion */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
  --motion-fast: 120ms; --motion-base: 200ms; --motion-slow: 300ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg: #0F172A;
    --color-surface: #1E293B;
    --color-text: #E2E8F0;
    --color-text-muted: #94A3B8;
    --color-primary: #60A5FA;   /* variante clara indicada en MASTER.md para texto/enlaces */
    --color-on-primary: #0F172A;
  }
}

:root[data-theme="dark"] {
  /* mismos valores que el bloque anterior, para el toggle manual */
}

@media (prefers-reduced-motion: reduce) {
  :root { --motion-fast: 0.01ms; --motion-base: 0.01ms; --motion-slow: 0.01ms; }
}

body {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: var(--text-body);
  line-height: var(--leading-body);
}

:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
:focus:not(:focus-visible) { outline: none; }

/* Superficies del navegador: lo que no dibujaste tambien lleva el sistema */
::selection { background: color-mix(in srgb, var(--color-primary) 25%, transparent); color: var(--color-text); }
input, textarea { caret-color: var(--color-primary); }
html { scrollbar-color: var(--color-text-muted) var(--color-surface); scrollbar-width: thin; }
a { text-decoration-thickness: 1px; text-underline-offset: 0.15em; }
.num, td.num, .precio { font-variant-numeric: tabular-nums; }
```

## Tailwind

Configuracion clasica (`tailwind.config.js`):

```js
module.exports = {
  darkMode: ["selector", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: "var(--color-primary)",
        "on-primary": "var(--color-on-primary)",
        surface: "var(--color-surface)",
        bg: "var(--color-bg)",
        text: "var(--color-text)",
        muted: "var(--color-text-muted)",
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        error: "var(--color-error)",
      },
      spacing: { 1: "var(--space-1)", 2: "var(--space-2)", 3: "var(--space-3)", 4: "var(--space-4)", 6: "var(--space-6)", 8: "var(--space-8)", 12: "var(--space-12)", 16: "var(--space-16)" },
      borderRadius: { sm: "var(--radius-sm)", md: "var(--radius-md)", lg: "var(--radius-lg)" },
    },
  },
};
```

Configuracion basada en CSS (`@theme`): declarar `--color-primary`, `--spacing-4`, etc. dentro
de `@theme { }` con los mismos valores; las clases `bg-primary`, `p-4` salen de ahi.

Uso en componentes: `bg-surface text-text`, `text-primary`, `p-4`. Prohibido `bg-[#2563EB]`.

## Test de contraste (RED primero)

Sin dependencias, con el runner del proyecto (ejemplo con el runner de Node):

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/tokens.css", import.meta.url), "utf8");
const token = (name) => css.match(new RegExp(`${name}:\\s*(#[0-9A-Fa-f]{6})`))[1];

const lin = (c) => { const s = c / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; };
const lum = (hex) => { const n = parseInt(hex.slice(1), 16); return 0.2126 * lin(n >> 16 & 255) + 0.7152 * lin(n >> 8 & 255) + 0.0722 * lin(n & 255); };
const ratio = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };

test("texto sobre fondo claro cumple AA", () => assert.ok(ratio(token("--color-text"), token("--color-bg")) >= 4.5));
test("on-primary sobre primary cumple AA", () => assert.ok(ratio(token("--color-on-primary"), token("--color-primary")) >= 4.5));
```

Si el proyecto no tiene runner JS, verificar con el catalogo del plugin:

```bash
python -c "import sys; sys.path.insert(0, r'${CLAUDE_PLUGIN_ROOT}/scripts'); import catalog; print(catalog.contrast_ratio('#0F172A', '#FFFFFF'))"
```

## Imagenes y motion

Todo `<img>` con `width`, `height` y `loading="lazy"` salvo el hero; animar solo `transform` y
`opacity` con `var(--motion-*)`; el bloque `prefers-reduced-motion` de `tokens.css` cubre el
resto.
