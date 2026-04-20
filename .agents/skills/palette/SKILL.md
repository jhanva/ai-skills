---
name: palette
description: >-
  Gestiona color palettes para pixel art: crear base palette con ramps, definir palette swap
  variants (enemy recolors, equipment tiers, seasons), validar reglas (max colors, outline,
  no AA), y exportar en GPL/JSON. Output: design/palette.md o design/palettes/{name}.md
---

# Palette Management

Crear, validar, y gestionar color palettes para pixel art. Output: `design/palette.md` + archivos GPL/JSON.

## FASE 1: Determinar modo

| Modo | Argumento | Accion |
|------|-----------|--------|
| Crear | `crear` | Base palette nueva (FASES 2-6) |
| Swap | `swap` | Palette swap variants (FASE 7) |
| Revisar | `revisar` | Validar palette existente (FASE 8) |

Si no hay argumento, preguntar.

## FASE 2: Leer art-bible [CREAR]

Extraer restricciones de `design/art-bible.md`: max colors, outline color, AA policy, palette philosophy.

Defaults si no hay art-bible: 32 colores, outline negro, AA prohibido.

## FASE 3: Definir categorias [CREAR]

Categorias funcionales: Skin (4-6 colores), Nature (6-8), Earth (4-6), Water (3-4), Metal (4-5), UI (4-6), Accent (3-5).

Total debe estar <= max colors del art-bible.

## FASE 4: Color ramps [CREAR]

Cada categoria tiene ramp shadow→base→highlight (3-5 tonos).

Reglas:
- **Hue shifting**: shadow shift hacia azul/purpura (no solo "mas oscuro")
- **Saturation**: highlight mas saturado, shadow menos
- **Value steps**: incrementos consistentes, sin jumps bruscos
- **Readable**: distinguible a 1x scale

Tabla: `category → ramp name → deep shadow → shadow → base → highlight → shine`.

## FASE 5: Validar reglas [CREAR]

Checklist:
- Total colors <= max del art-bible
- UI text contrast ratio >= 4.5:1 (WCAG AA)
- Outline contrasta con todos los base colors
- Ramps de 3-5 tonos (no 2 ni 6+)
- Value steps consistentes (<30% lightness jump)
- Palette cubre espectro (no todo greens/browns)
- Accent colors distinguibles
- Sin duplicates entre categories
- Colores distinguibles a 1x scale

Warnings: >48 colores, ramps de 2 tonos, >10 accent colors.

## FASE 6: Export [CREAR]

Generar 3 archivos con misma taxonomia:
- `design/palette.gpl`: ordenada por categoria, legible en Aseprite
- `design/palette.json`: categorias, hex values, reglas
- `design/palette.md`: decision log y documentacion

## FASE 7: Palette swap [SWAP]

Definir remapping para variants (enemy recolors, equipment tiers, seasons, status effects).

Tabla: `variant → purpose → color remap → notes`. JSON con remaps por variant.

Metodo de implementacion: shader (runtime swap) o assets separados (duplicar sprite con colores swapped, mas filesize pero no depende de shaders).

## FASE 8: Revisar palette [REVISAR]

Leer palette actual, extraer hex values, ejecutar validaciones de FASE 5. Detectar: colores muy similares (<10% distance HSV), ramps con gaps, accent colors con baja saturacion.

Report en conversacion con PASS/FAIL por regla y recomendaciones.

## FASE 9: Generar palette document [CREAR]

Leer `references/output-template.md` para estructura y validacion final.

## Transicion

Siguientes pasos: `$sprite-spec`, `$tileset-spec`, o `$palette swap`.
