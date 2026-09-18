---
name: ui-tokens
description: >
  Materializa el sistema de diseno persistido (design-system/<proyecto>/MASTER.md) en
  tokens de codigo del stack: Color/Type/Shape/Spacing y Theme para Jetpack Compose, o
  custom properties CSS y tema Tailwind para web. Genera tambien la prueba de contraste
  que fija los pares texto/fondo. Usar cuando: el usuario dice "genera los tokens",
  "crea el theme", "pasa el design system a codigo", "tokens css", "MaterialTheme".
argument-hint: "[ruta a MASTER.md o nombre de proyecto] [--stack compose|web]"
disable-model-invocation: true
---

# UI Tokens — Del sistema de diseno al codigo

`MASTER.md` es la fuente de verdad; este skill lo traduce a archivos de tokens que los
componentes consumen por nombre. Nunca al reves: si hace falta un color nuevo, primero se
anade a `MASTER.md` (con `/design-system`) y despues se regenera.

## Precondiciones

1. Localizar el sistema: argumento, o `Glob design-system/**/MASTER.md`. Si no existe,
   detenerse y proponer `/design-system`; no inventar tokens.
2. Leer `MASTER.md` completo: secciones Color, Tipografia, Espaciado, Motion y Stack.
3. Detectar el stack como en `/design-system`. Localizar donde viven los tokens actuales, si
   los hay (`ui/theme/` en Compose; `tokens.css`, `theme.css` o `tailwind.config.*` en web).
   Si existen, se **actualizan**, no se duplican.

## Proceso (bajo /tdd)

Los tokens son codigo de produccion y se escriben con test primero:

1. **RED**: prueba de contraste que lee los pares del sistema (texto/fondo claro, texto/fondo
   oscuro, on-primary/primary) y falla porque el archivo de tokens no existe. Plantilla en
   `${CLAUDE_PLUGIN_ROOT}/skills/ui-tokens/references/compose-tokens.md` o `web-tokens.md`.
2. **GREEN**: generar los archivos de tokens con los valores exactos de `MASTER.md`.
3. **REFACTOR**: reemplazar literales existentes en componentes por los tokens, uno por uno,
   con `Grep` de `Color(0x` / `#[0-9A-Fa-f]{6}` / `\.sp\b` fuera del directorio de tema.

### Compose

Archivos (en el paquete de tema del proyecto): `Color.kt`, `Type.kt`, `Shape.kt`, `Spacing.kt`,
`Theme.kt`. `Theme.kt` expone `AppTheme(darkTheme, content)` con `lightColorScheme` y
`darkColorScheme`; `dynamicColor` desactivado salvo que `MASTER.md` lo autorice (rompe el
contraste validado). Estructura y ejemplos en `references/compose-tokens.md`.

### Web

Archivos: `tokens.css` con `:root`, `@media (prefers-color-scheme: dark)` y
`[data-theme="dark"]`; si hay Tailwind, `theme.extend` apuntando a las variables. La escala
tipografica con `clamp`. Estructura y ejemplos en `references/web-tokens.md`.

## Verificacion antes de cerrar

- El test de contraste pasa (leer el output, no asumirlo).
- `Grep` de literales de color y tamano fuera del directorio de tema devuelve cero o una lista
  justificada (imagenes de marca, casos documentados).
- Los nombres de tokens coinciden con los de `MASTER.md`; si se anadio alguno, se anota en
  `MASTER.md` en la misma tarea.

Reportar archivos creados o modificados, resultado del test y literales que quedaron pendientes.

Argumento recibido: $ARGUMENTS
