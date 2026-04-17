---
name: art-bible
description: >
  Definir art bible para pixel art: resolucion, tile/character size,
  paleta (16-32 colores), estilo de sprites, reglas de animacion,
  UI style. Produce art-bible.md.
when_to_use: >
  Cuando el usuario quiere definir la estetica de un juego pixel art,
  o cuando dice "art-bible", "paleta", "estilo visual", "pixel art",
  "resolucion", "sprites", "definir arte".
argument-hint: "[estilo o referencia visual]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
agent: pixel-artist
---

# Art Bible — Definir estetica pixel art

## Objetivo

Crear la biblia de arte del proyecto: convenciones de resolucion, paleta,
estilo de sprites, animaciones, y UI. Este documento asegura consistencia
visual en todo el juego. El output es `design/art-bible.md`.

---

## FASE 1: Leer game-concept.md

Buscar y leer `design/gdd/game-concept.md` para extraer:

- Look & Feel (estetica declarada)
- Genero (RPG, platformer, roguelike, etc.)
- Target platform (PC, mobile, web)

Si NO existe game-concept.md, preguntar:

```
No encontre design/gdd/game-concept.md.

¿Quieres que infiera el concepto del argumento ("[argumento]"),
o prefieres correr `/game-concept` primero?

a) Inferir del argumento (continuar sin game-concept.md)
b) Pausar y correr /game-concept primero
```

---

## FASE 2: Definir resolucion base

Presentar opciones con tradeoffs:

```
## Resolucion y grid

La resolucion base define TODA la estetica. Elegir UNA y no cambiarla.

### Opcion A: Tiles 8x8, Characters 16x16
- Estetica: Muy retro (NES-era), minimalista
- Detalle: Muy bajo, iconico
- Produccion: Rapida (pocos pixels por sprite)
- Mejor para: juegos muy estilizados, mobile, o con muchos assets
- Ejemplo: Downwell, Minit

### Opcion B: Tiles 16x16, Characters 32x32
- Estetica: Clasico SNES/GBA-era
- Detalle: Medio, expresivo
- Produccion: Balance entre detalle y velocidad
- Mejor para: RPGs, platformers clasicos
- Ejemplo: Celeste, Stardew Valley, Undertale

### Opcion C: Tiles 16x16, Characters 48x48
- Estetica: Hibrido (tiles retro, characters detallados)
- Detalle: Alto en characters, tiles simples
- Produccion: Mas lenta en characters
- Mejor para: games enfocados en characters (visual novels, boss fights)
- Ejemplo: Shovel Knight

### Opcion D: Custom (especifica)
- Tiles: [size] x [size]
- Characters: [size] x [size]

¿Que resolucion usaras?
```

Guardar: `TILE_SIZE`, `CHARACTER_SIZE`

### Render resolution

Basado en la resolucion elegida, calcular viewport:

```
## Render Resolution

Basado en tiles [TILE_SIZE]x[TILE_SIZE]:

Opcion recomendada (16:9):
  Base: 256x144 (16 tiles × 9 tiles visibles)
  Scale: integer only (2x, 3x, 4x, 5x)
  → 512x288 (2x), 768x432 (3x), 1024x576 (4x)

Device mapping:
  720p  → 5x scale
  1080p → 7x scale (pillarbox para 16:9 exacto)
  1440p → 10x scale

¿Usar base 256x144? (si/no/custom)
```

---

## FASE 3: Definir paleta

```
## Paleta de colores

Pixel art clasico usa paletas limitadas (16-32 colores max) para cohesion.

### Filosofia de paleta

Opcion A: Paleta estricta (16 colores)
  - TODOS los sprites usan solo estos 16 colores
  - Maxima cohesion visual
  - Requiere disciplina en arte
  - Ejemplo: Pico-8 (16 colores fijos)

Opcion B: Paleta guia (24-32 colores)
  - Paleta base + variaciones permitidas
  - Flexibilidad para casos especiales
  - Cohesion alta pero no absoluta
  - Ejemplo: Celeste, Hyper Light Drifter

¿Paleta estricta (16) o guia (24-32)?
```

### Categorias de color

Proponer paleta basada en Look & Feel del game-concept.md:

```
## Propuesta de Paleta

Basado en "[look & feel del concepto]":

### Skin/Organic (2-3 tonos)
  #f2d3ab  (highlight)
  #c69c6d  (base)
  #8b6f47  (shadow)

### Nature (3-4 tonos)
  #8fde5d  (bright green)
  #5ab552  (base green)
  #2d6e2d  (dark green)
  #1a4a1a  (deep shadow)

### Metals/Stone (3 tonos)
  #8c8fae  (highlight)
  #4e4e6e  (base)
  #2c2c3e  (shadow)

### Water/Sky (2-3 tonos)
  #6bb5d6  (light blue)
  #3978a8  (base blue)
  #1e5080  (deep blue)

### Fire/Warm (2 tonos)
  #e8832a  (flame orange)
  #b84a28  (ember red)

### UI/Text (3 tonos)
  #f0f0f0  (white/highlight)
  #8b8b8b  (mid gray)
  #222222  (black/shadow)

### Accent (1-2 tonos)
  #e64539  (red alert)
  #ffd700  (gold treasure)

TOTAL: [calcular] colores

¿Ajustar paleta? (agregar/quitar/cambiar colores)
```

---

## FASE 4: Estilo de sprites

```
## Reglas de estilo para sprites

### Outline
a) No outline (color directo, estilo NES)
b) Black outline (#000000, estilo GBA/SNES)
c) Colored outline (outline del color shadow, estilo moderno)

¿Que estilo?

### Shading
a) Flat (1 color por area, sin sombras — estilo minimalista)
b) Pillow shading (sombra en bordes, estilo principiante — EVITAR)
c) Directional shading (luz de una direccion, estilo clasico)
d) Dithering (patron de pixels para transiciones)

¿Que shading?

### Anti-aliasing
a) NO anti-aliasing (bordes duros, pixel puro)
b) Selective AA (solo en curvas criticas, manual)

Recomendacion: NO anti-aliasing para pixel art clasico.

### Pixel density
Regla: TODOS los sprites deben tener el mismo "pixels per unit".
Un character 32x32 NO debe tener mas detalle que un tile 16x16
escalado 2x.

Validacion: sprites visualmente consistentes cuando se renderizan
juntos en la misma escena.
```

---

## FASE 5: Reglas de animacion

```
## Animacion de sprites

### Frame counts por estado

Basado en el genero ("[genero]"), definir frame counts standard:

| Estado | Frames | Loop | FPS | Notas |
|---|---|---|---|---|
| idle | 2-4 | si | 2-4 | Sutil (respiracion, parpadeo) |
| walk | 4-6 | si | 8-12 | Ciclo completo de paso |
| run | 6-8 | si | 12-16 | Mas rapido que walk |
| jump | 3-4 | no | — | Anticipation → air → land |
| attack | 3-5 | no | 12-15 | Windup → strike → recovery |
| hurt | 2 | no | 10 | Flash + recoil |
| death | 4-6 | no | 8 | Colapso, hold ultimo frame |

Agregar/quitar estados segun el genero.

### Frame timing

Opcion A: Fixed frame duration (simple)
  - Todos los frames de una animacion duran lo mismo
  - Ejemplo: walk = 4 frames × 0.1s = 0.4s loop

Opcion B: Variable frame duration (avanzado)
  - Frames pueden durar diferente (hold en anticipation)
  - Ejemplo: attack = [0.15s, 0.05s, 0.1s, 0.2s]
  - Requiere data-driven animation system

¿Fixed o variable frame duration?

### Direcciones

Opcion A: 4-way (down, up, left, right)
  - Left/right: flip horizontal del mismo sprite
  - Total: 3 sprite sets por animacion (down, up, left+right)

Opcion B: 8-way (N, NE, E, SE, S, SW, W, NW)
  - Mas trabajo de arte, movimiento mas fluido
  - Total: 5 sprite sets (4 diagonales usan flip)

Recomendacion para solo dev: 4-way (menos arte).
```

---

## FASE 6: Restricciones tecnicas

```
## Restricciones pixel-perfect

Estas reglas son OBLIGATORIAS para mantener pixel art limpio:

| Regla | Implementacion Godot 4 |
|---|---|
| Integer scaling ONLY | `window/stretch/mode = "canvas_items"` |
| Nearest-neighbor filter | `rendering/textures/canvas_textures/default_texture_filter = 0` |
| No rotaciones sub-pixel | Sprites solo 0°/90°/180°/270° o pre-render rotaciones |
| Camera snap to pixel grid | `camera.position = camera.position.round()` cada frame |
| Consistent pixels-per-unit | Todos los sprites importados con mismo PPU |

### Import settings (Godot 4)

Todos los sprites deben importarse con:
```
Filter: Nearest
Repeat: Disabled
sRGB: Disabled (si usas paletas indexadas)
Compress: Lossless
```

### Atlas packing

NO empaquetar automaticamente. Usar TextureAtlas manual:
- Padding minimo: 2px entre sprites
- Max size: 2048x2048 (mobile compatibility)
- Separar por contexto (characters.png, enemies.png, tiles.png, ui.png)
```

---

## FASE 7: UI style

```
## UI pixel art

### Panel/Window style

Opcion A: 9-patch con borde pixel
  - Border: 3-4px de ancho
  - Esquinas NO se estiran, bordes se repiten
  - Godot: NinePatchRect con texture region

Opcion B: Solid color con outline de 1px
  - Minimalista, menos arte necesario
  - Godot: ColorRect + outline shader

¿Que estilo de panel?

### Font

Opcion A: Bitmap font (pixel font)
  - Consistente con estetica pixel
  - Tamano fijo (8px, 16px, no escalable)
  - Herramienta: BMFont, Hiero, Aseprite

Opcion B: Vector font con pixel rendering
  - Flexible (escalable)
  - Filtrado nearest para simular pixel
  - Menos autentico

Recomendacion: bitmap font para pixel art puro.

Tamano: multiplo del pixel size base (8px o 16px, NO 12px ni 14px)

### Icon size

Regla: icons deben ser del tamano de 1 tile.

Si tile = 16x16 → icons = 16x16
Si tile = 8x8 → icons = 8x8

UI icons: items, skills, status effects, menu cursors
```

---

## FASE 8: Escribir art-bible.md

Generar documento en `design/art-bible.md`:

```markdown
# Art Bible — [Nombre del Juego]

## Vision

[2-3 frases del Look & Feel del game-concept.md]

---

## Resolucion

**Tile size:** [X]x[X] pixels

**Character size:** [Y]x[Y] pixels

**Base resolution:** [W]x[H] (aspect ratio 16:9)

**Scaling:** Integer only (2x, 3x, 4x, 5x)

**Target resolutions:**
- 720p: [scale]x
- 1080p: [scale]x
- 1440p: [scale]x

---

## Paleta

**Tipo:** [Estricta 16 colores | Guia 24-32 colores]

**Colores:**

### Skin/Organic
```
#f2d3ab  ██  highlight
#c69c6d  ██  base
#8b6f47  ██  shadow
```

### Nature
```
#8fde5d  ██  bright green
#5ab552  ██  base green
#2d6e2d  ██  dark green
#1a4a1a  ██  deep shadow
```

[... resto de categorias ...]

**TOTAL:** [N] colores

**Formato export:** PNG indexed (palette embedded) o paleta separada en .pal

---

## Estilo de Sprites

**Outline:** [No outline | Black outline | Colored outline]

**Shading:** [Flat | Directional | Dithering]

**Anti-aliasing:** NO (pixel art puro)

**Pixel density:** Consistente — todos los sprites con mismo PPU

**Direcciones:** [4-way | 8-way]

---

## Animaciones

### Frame counts standard

| Estado | Frames | Loop | FPS | Notas |
|---|---|---|---|---|
| idle | [N] | si | [fps] | [descripcion] |
| walk | [N] | si | [fps] | [descripcion] |
| attack | [N] | no | [fps] | [descripcion] |
| hurt | [N] | no | [fps] | [descripcion] |
| death | [N] | no | [fps] | [descripcion] |

### Frame timing

[Fixed frame duration | Variable frame duration]

Fixed: todos los frames duran lo mismo por animacion
Variable: frames individuales pueden durar diferente (data-driven)

### Naming convention

```
{entity}_{animation}_{direction}_{frame}.png

Ejemplos:
  player_idle_down_0.png
  player_walk_left_3.png
  slime_attack_0.png
```

---

## Restricciones Tecnicas

### Godot 4 settings

```gdscript
# project.godot
[rendering]
textures/canvas_textures/default_texture_filter = 0  # Nearest

[display]
window/size/viewport_width = [base_width]
window/size/viewport_height = [base_height]
window/stretch/mode = "canvas_items"
window/stretch/aspect = "keep"
```

### Import settings (sprites)

```
Filter: Nearest
Repeat: Disabled
Compress: Lossless
sRGB: Disabled
```

### Camera snapping

```gdscript
# En _process(delta) del camera controller:
position = position.round()
```

### Atlas organization

Separar por contexto:

- `characters.png` — player, NPCs (siempre cargados)
- `enemies.png` — enemy sprites (cargados en combate)
- `tiles.png` — tilesets (cargados por zona)
- `ui.png` — icons, panels, fonts (siempre cargados)

Max size: 2048x2048, padding 2px

---

## UI Style

**Panels:** [9-patch con borde | Solid color con outline]

**Font:** [Bitmap font | Vector pixel-style]
  - Tamano: [8px | 16px]
  - Nombre: [font file]

**Icon size:** [tile_size]x[tile_size] ([N]x[N])

**Cursor:** [descripcion del cursor sprite]

---

## Reglas de Produccion

### Checklist por sprite

- [ ] Tamano correcto ([CHARACTER_SIZE]x[CHARACTER_SIZE])
- [ ] Paleta respetada (solo colores de art-bible)
- [ ] Outline consistente ([estilo declarado])
- [ ] Shading consistente (luz desde [direccion])
- [ ] Exported como PNG indexado
- [ ] Naming convention correcta

### Validacion visual

Antes de integrar sprites:

1. Renderizar juntos en escena test
2. Verificar pixel density consistente
3. Verificar que no hay blur (texture filter nearest)
4. Verificar que animaciones loop sin saltos

---

## Referencias Visuales

**Juegos de referencia:**
- [Juego 1] — [aspecto especifico: paleta, shading, animaciones]
- [Juego 2] — [aspecto especifico]

**Arte de referencia:**
- [Link o descripcion de arte inspiracional]

---

## Anti-Patrones

```
ANTI-PATRON: Mezclar resolucion (sprites 16x16 con 24x24)
  Solucion: todo al mismo base size

ANTI-PATRON: Linear filtering en sprites
  Solucion: texture filter = Nearest SIEMPRE

ANTI-PATRON: Paleta inconsistente (cada sprite con colores diferentes)
  Solucion: paleta estricta, validar antes de integrar

ANTI-PATRON: Animaciones sin timing consistente
  Solucion: tabla de FPS standard por tipo de animacion

ANTI-PATRON: Sub-pixel positioning sin camera snap
  Solucion: camera.position.round() cada frame
```

---

## Siguientes Pasos

1. `/pixel-pipeline` — Disenar workflow de Aseprite a Godot
2. Crear sprite placeholders (solid color boxes del tamano correcto)
3. Iterar arte siguiendo este art-bible
4. `/plan` — Convertir game-concept + art-bible en tareas
```

Escribir archivo completo con valores basados en las respuestas del usuario.

---

## FASE 9: Transicion

```
## Art Bible completado

Archivo creado: design/art-bible.md

Este documento es la biblia visual del proyecto. TODOS los assets
deben seguir estas reglas.

## Siguientes pasos recomendados

### Opcion A: Disenar pipeline de assets
Usa `/pixel-pipeline` para definir el flujo completo de Aseprite
a Godot: export settings, atlas packing, animation data.

### Opcion B: Disenar sistema de juego
Usa `/design-system <nombre>` para disenar una mecanica MVP
(inventario, dialogo, crafting, etc.).

### Opcion C: Planificar implementacion
Si game-concept.md + art-bible.md estan completos, usa `/plan`
para convertirlos en tareas de implementacion.

¿Que hacemos ahora?
```

NO ejecutar automaticamente. Esperar decision del usuario.

---

## Anti-patrones

```
ANTI-PATRON: Paleta con 50+ colores
  → Pierde cohesion visual, no parece pixel art
  Solucion: max 32 colores, preferir 16-24

ANTI-PATRON: No definir pixel density
  → Sprites de diferente "resolucion visual" mezclados
  Solucion: regla explicita de PPU consistente

ANTI-PATRON: Permitir rotaciones arbitrarias
  → Pixels deformados, rompe pixel-perfect
  Solucion: solo 0/90/180/270, o pre-render rotaciones

ANTI-PATRON: No documentar frame counts
  → Cada animacion con timing diferente, inconsistencia
  Solucion: tabla standard de frames por estado

ANTI-PATRON: Linear filtering "por defecto"
  → Sprites borrosos, bleeding entre frames
  Solucion: texture filter Nearest en settings globales
```

## Argumento: $ARGUMENTS
