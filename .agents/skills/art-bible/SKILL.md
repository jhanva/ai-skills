---
name: art-bible
description: >-
  Definir art bible para pixel art: resolucion, tile/character size, paleta (16-32 colores),
  estilo de sprites, reglas de animacion, UI style. Produce art-bible.md. Usala cuando el
  usuario quiere definir la estetica de un juego pixel art, o cuando dice "art-bible",
  "paleta", "estilo visual", "pixel art", "resolucion", "sprites", "definir arte".
---

# Art Bible

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$art-bible`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Cuando un ejemplo heredado mencione tools de Claude, aplica la traduccion de `AGENTS.md` y expresa la accion con herramientas reales de Codex (`rg`, `find`, `sed -n`, shell puntual y patch nativo).

Crear la biblia de arte del proyecto: convenciones de resolucion, paleta, estilo de sprites, animaciones, y UI. Asegura consistencia visual. Output: `design/art-bible.md`.

## FASE 1: Leer game-concept.md

Buscar `design/gdd/game-concept.md` para extraer Look & Feel, genero, y target platform. Si no existe, preguntar si inferir del argumento o correr `$game-concept` primero.

## FASE 2: Definir resolucion base

Presentar opciones con tradeoffs:

| Opcion | Tiles | Characters | Estetica | Produccion | Ejemplo |
|--------|-------|------------|----------|------------|---------|
| A | 8x8 | 16x16 | NES-era, minimalista | Rapida | Downwell, Minit |
| B | 16x16 | 32x32 | Clasico SNES/GBA | Balance | Celeste, Stardew Valley |
| C | 16x16 | 48x48 | Hibrido (tiles retro, characters detallados) | Lenta en characters | Shovel Knight |
| D | Custom | Custom | — | — | — |

Calcular render resolution (viewport base, integer scaling, device mapping).

## FASE 3: Definir paleta

Elegir filosofia: estricta (16 colores, maxima cohesion) o guia (24-32, flexible).

Proponer paleta organizada por categorias funcionales: Skin/Organic (2-3 tonos), Nature (3-4), Metals/Stone (3), Water/Sky (2-3), Fire/Warm (2), UI/Text (3), Accent (1-2).

Confirmar con el usuario antes de continuar.

## FASE 4: Estilo de sprites

Definir reglas para:
- **Outline**: none (NES), black (GBA/SNES), colored (moderno)
- **Shading**: flat, directional (recomendado), dithering — NO pillow shading
- **Anti-aliasing**: NO para pixel art clasico (selective solo en curvas criticas)
- **Pixel density**: TODOS los sprites deben tener el mismo pixels-per-unit

## FASE 5: Reglas de animacion

Definir por estado: frame counts, FPS, loop, notas.

Reglas clave:
- Idle: loop, FPS bajo (6-8), sutil
- Walk/Run: loop, FPS medio (10-12), contact frames alineados con SFX
- Attack: no loop, FPS alto (12-16), marcar hitbox frames
- Hurt: no loop, corto (2-4 frames)
- Death: no loop, FPS medio, ultimo frame persiste

Elegir: fixed vs variable frame duration, 4-way vs 8-way directions.

Recomendacion para solo dev: 4-way + fixed.

## FASE 6: Restricciones tecnicas

Reglas OBLIGATORIAS para pixel-perfect:

| Regla | Implementacion Godot 4 |
|---|---|
| Integer scaling ONLY | `window/stretch/mode = "canvas_items"` |
| Nearest-neighbor filter | `default_texture_filter = 0` |
| No rotaciones sub-pixel | Solo 0/90/180/270 o pre-render |
| Camera snap to pixel grid | `position.round()` cada frame |
| Consistent pixels-per-unit | Mismo PPU en todos los sprites |

Import settings: Filter Nearest, Repeat Disabled, Compress Lossless.

Atlas packing: manual, 2px padding, max 2048x2048, separar por contexto.

## FASE 7: UI style

Definir:
- **Panel**: 9-patch con borde pixel (NinePatchRect) o solid + outline (ColorRect)
- **Font**: bitmap pixel font (recomendado, tamano multiplo del pixel base) o vector con nearest
- **Icon size**: mismo tamano que 1 tile

## FASE 8: Escribir art-bible.md

Escribir `design/art-bible.md`. Leer `references/output-template.md` para estructura, checklist por sprite, anti-patrones, y cierre.
