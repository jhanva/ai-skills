---
name: pixel-pipeline
description: Diseña pipelines de assets pixel art, sprites, tiles, atlas, paletas y exportación para integración en juegos. Úsala cuando el usuario pida explícitamente ayuda con assets pixel art. No la uses para arte raster general sin foco en pipeline pixel.
---

# Pixel Pipeline — Pipeline de assets pixel art

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$pixel-pipeline`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Objetivo

Disenar el flujo completo desde arte pixel art hasta juego funcional:
resolucion, sprite sheets, animaciones, tilesets, palette management,
y atlas packing. El output es una spec de pipeline y convenciones
lista para el equipo de arte y desarrollo.

---

## FASE 1: Definir convenciones base

### 1.1 Resolucion y grid

Elegir UNA resolucion base y mantenerla consistente:

| Resolucion | Uso tipico | Detalle |
|---|---|---|
| 8x8 | Muy retro (NES-era), items/icons | Poco detalle, rapido de producir |
| 16x16 | RPGs clasicos (SNES-era), tiles y characters | Buen balance detalle/produccion |
| 32x32 | RPGs modernos, mas detalle en characters | Mas expresivo, mas trabajo por sprite |
| 48x48 | Characters detallados sobre tiles 16x16 | Hibrido: tiles 16x16, characters 48x48 |

Regla: elegir UN tamano de tile y UN tamano de character. No mezclar.

```
Ejemplo:
  Tiles: 16x16
  Characters: 32x32 (2 tiles de alto, 2 de ancho)
  UI icons: 16x16
  Portraits: 64x64 (cuadro de dialogo)
```

### 1.2 Render resolution

```
Base resolution: 256x144 (16:9 con tiles 16x16 = 16x9 tiles visibles)
Scale factor: integer scaling only (2x, 3x, 4x)
  → 512x288, 768x432, 1024x576

Device resolution mapping:
  720p  → 5x scale (1280/256 = 5)
  1080p → 7x scale (1792/256 ≈ 7, pillarbox)
  1440p → 10x scale (2560/256 = 10)
```

### 1.3 Reglas de pixel-perfect

| Regla | Por que |
|---|---|
| Integer scaling ONLY | Fractional scaling = pixels de tamano desigual |
| Nearest-neighbor filtering | Linear filtering = blur en pixel art |
| No rotaciones sub-pixel | Rotar sprites solo 0/90/180/270 grados |
| Camera snap to pixel grid | Evitar shimmer en scroll |
| Consistent pixel size | Todos los assets al mismo pixels-per-unit |

---

## FASE 2: Sprite sheets y animaciones

### 2.1 Naming convention

```
{entity}_{animation}_{frame}.png

Ejemplos:
  player_idle_0.png
  player_idle_1.png
  player_walk_0.png
  player_walk_1.png
  player_walk_2.png
  player_walk_3.png
  player_attack_0.png
  player_attack_1.png
  player_attack_2.png
  slime_idle_0.png
  slime_hurt_0.png
```

Este naming permite que TexturePacker agrupe automaticamente por entity+animation.

### 2.2 Animation states standard

Definir set minimo de animaciones por tipo de entity:

**Player / Party members:**

| Estado | Frames | Loop | Notas |
|---|---|---|---|
| idle | 2-4 | si | Sutil movimiento (respiracion) |
| walk_down | 4 | si | Direccion default |
| walk_up | 4 | si | |
| walk_left | 4 | si | walk_right = flip horizontal |
| attack | 3-5 | no | Anticipation → strike → recovery |
| hurt | 2 | no | Flash + knockback |
| death | 4-6 | no | Colapso, ultimo frame se mantiene |
| cast | 3-4 | no | Para skills/magic |

**Enemies (batalla por turnos, no necesitan walk):**

| Estado | Frames | Loop | Notas |
|---|---|---|---|
| idle | 2-4 | si | Movimiento amenazante sutil |
| attack | 3-5 | no | Lunge/strike |
| hurt | 2 | no | Flash |
| death | 4-6 | no | Dissolve/colapso |
| special | 3-5 | no | Para skills unicos (bosses) |

**NPCs:**

| Estado | Frames | Loop | Notas |
|---|---|---|---|
| idle | 2 | si | Minimo esfuerzo |
| talk | 2-3 | si | Boca abierta/cerrada |

### 2.3 Animation data (data-driven)

```json
{
  "player": {
    "idle": {
      "frames": ["player_idle_0", "player_idle_1"],
      "frameDuration": 0.5,
      "loop": true
    },
    "walk_down": {
      "frames": ["player_walk_down_0", "player_walk_down_1",
                  "player_walk_down_2", "player_walk_down_3"],
      "frameDuration": 0.15,
      "loop": true
    },
    "attack": {
      "frames": ["player_attack_0", "player_attack_1", "player_attack_2"],
      "frameDuration": 0.1,
      "loop": false
    }
  }
}
```

### 2.4 Animation controller

```kotlin
class AnimationController(private val animations: Map<String, AnimationData>) {
    private var current: String = "idle"
    private var stateTime: Float = 0f
    private var onComplete: (() -> Unit)? = null

    fun play(name: String, onComplete: (() -> Unit)? = null) {
        if (name == current) return
        current = name
        stateTime = 0f
        this.onComplete = onComplete
    }

    fun update(delta: Float): TextureRegion {
        stateTime += delta
        val anim = animations[current]!!
        val frame = anim.getFrame(stateTime)

        if (!anim.loop && anim.isFinished(stateTime)) {
            onComplete?.invoke()
            onComplete = null
        }

        return frame
    }

    val isPlaying: Boolean
        get() = animations[current]?.let { !it.loop && !it.isFinished(stateTime) } ?: false
}
```

---

## FASE 3: Tilesets y tilemaps

### 3.1 Tileset organization

```
tiles/
  terrain.png        → grass, water, dirt, stone (autotile)
  buildings.png      → walls, floors, roofs, doors
  decorations.png    → trees, flowers, furniture
  interactables.png  → chests, signs, levers
```

### 3.2 Autotiling (bitmasking)

Para tiles que se conectan (agua, paredes, caminos):

```
Bitmask 4-bit (basico, 16 tiles):
  Cada tile revisa 4 vecinos (N, E, S, W)
  bit = 1 si vecino es mismo tipo
  index = N*1 + E*2 + S*4 + W*8
  → 16 variantes por tile type

Bitmask 8-bit (completo, 47 tiles):
  Tambien revisa diagonales (NE, SE, SW, NW)
  → 47 variantes unicas (de 256 posibles, con simetrias)
  → Mejor apariencia, mas trabajo de arte
```

Recomendacion: empezar con 4-bit (16 tiles), migrar a 8-bit si el juego lo necesita.

### 3.3 Tiled editor integration

```
Workflow:
  1. Crear tileset en Aseprite (exportar como PNG)
  2. Importar PNG en Tiled, definir tile properties
  3. Pintar mapa con layers:
     - ground     (z=0, siempre debajo)
     - objects    (z=1, arboles, rocas)
     - above      (z=2, techos, copas de arboles — sobre player)
     - collision  (invisible, marca tiles no-walkable)
     - events     (invisible, triggers: spawn, door, dialog)
  4. Exportar como TMX
  5. LibGDX carga TMX con TmxMapLoader
```

### 3.4 Collision layer

```kotlin
fun isWalkable(tileX: Int, tileY: Int): Boolean {
    val collisionLayer = map.layers["collision"] as TiledMapTileLayer
    return collisionLayer.getCell(tileX, tileY) == null  // null = walkable
}

// Pathfinding: A* sobre grid de tiles
fun findPath(start: TilePos, end: TilePos): List<TilePos> {
    // A* con isWalkable como constraint
    // Heuristic: Manhattan distance (4-way) o Chebyshev (8-way)
}
```

---

## FASE 4: Palette management

### 4.1 Palette definition

Definir paleta global del juego (16-32 colores max para cohesion):

```
Paleta base (ejemplo 16 colores):
  Skin: #f2d3ab, #c69c6d
  Hair: #4a3728, #2a1f14
  Metals: #8c8fae, #4e4e6e, #2c2c3e
  Nature: #5ab552, #2d6e2d, #1a4a1a
  Water: #3978a8, #1e5080
  Fire: #e8832a, #b84a28
  UI: #f0f0f0, #222222
  Accent: #e64539
```

### 4.2 Palette swapping via shader

Recolorear sprites en runtime sin duplicar arte:

```glsl
// Fragment shader
uniform sampler2D u_texture;      // sprite original
uniform sampler2D u_palette;      // lookup texture (1xN)
uniform float u_paletteRow;       // cual paleta usar (0.0 = base, 0.5 = alt)

void main() {
    vec4 color = texture2D(u_texture, v_texCoord);

    // Usar canal rojo como indice en la lookup texture
    float index = color.r;
    vec4 swapped = texture2D(u_palette, vec2(index, u_paletteRow));

    gl_FragColor = vec4(swapped.rgb, color.a);
}
```

### 4.3 Uso de palette swap

| Uso | Ejemplo |
|---|---|
| Variantes de enemigos | Slime verde → azul → rojo (3 dificultades) |
| Equipo visible | Armadura base → iron → gold (cambio de paleta) |
| Estaciones/tiempo | Arboles verdes → naranjas → blancos (nieve) |
| Status effects | Character → tinte rojo (poison), azul (frozen) |
| Team colors | Mismo sprite, colores de faccion diferentes |

### 4.4 Reglas de paleta

| Regla | Por que |
|---|---|
| Sprites indexados a paleta | Habilita palette swap via shader |
| Max 4-8 colores por sprite | Pixelart se ve mejor con pocos colores |
| Ramps de 3-4 tonos | Shadow → base → highlight → bright |
| Outline color consistente | Negro puro (#000) o near-black (#1a1a2e) |
| No anti-aliasing | Pixel art usa bordes duros, AA rompe la estetica |

---

## FASE 5: TextureAtlas y packing

### 5.1 Workflow minimo

- Exportar sprite sheets desde Aseprite con tags por animacion
- Empaquetar con atlas, nunca con texturas sueltas en produccion
- Mantener `Nearest`, padding >= 2 y atlas razonables para mobile

### 5.2 Atlas por contexto

No empaquetar TODO en un solo atlas. Separar por uso:

```
characters.atlas  → player, party, NPCs (siempre cargados en explore)
enemies.atlas     → sprites de enemigos (cargados en batalla)
tiles.atlas       → tilesets (cargados por zona/mapa)
ui.atlas          → iconos, frames, fonts (siempre cargados)
effects.atlas     → particulas, spell effects (cargados en batalla)
```

### 5.3 Memory budget

```
Atlas 2048x2048 RGBA = 16MB en VRAM
Atlas 1024x1024 RGBA = 4MB en VRAM

Budget para mobile:
  Characters: 1x 1024x1024 = 4MB
  Enemies:    1x 1024x1024 = 4MB
  Tiles:      1x 2048x2048 = 16MB (zona actual)
  UI:         1x 1024x1024 = 4MB
  Effects:    1x 512x512   = 1MB
  TOTAL: ~29MB VRAM en peak (batalla)

Regla: total atlas VRAM < 64MB en mobile
```

---

## FASE 6: UI pixel art

### 6.1 9-patch para panels

```
Crear 9-patch en Aseprite:
  - Tamano minimo: esquinas + 1px de borde repetible
  - Ejemplo: dialog box con borde de 3px
    → Imagen: 9x9 minimo (3+3+3 horizontal, 3+3+3 vertical)
    → Las esquinas no se estiran
    → Los bordes se repiten/estiran
    → El centro se llena

En LibGDX:
  NinePatch(atlas.findRegion("dialog_box"), 3, 3, 3, 3)
```

### 6.2 Pixel font

```
Opciones:
  1. Bitmap font generado con BMFont/Hiero
     → Export como .fnt + .png
     → Asegurar Nearest filtering

  2. Pixel font sprite sheet
     → Cada caracter como region en atlas
     → Alineado a grid (monospace recomendado para pixel)

Regla: tamano de font = multiplo del pixel size base
  Si pixel = 1 unit, font size = 8 o 16 (nunca 12, 14, etc.)
```

---

## FASE 7: Validacion

Antes del cierre, lee `references/output-template.md` para usar la checklist completa y revisar los anti-patrones relevantes.

Valida como minimo:
- consistencia de paleta y resoluciones
- `Nearest` + integer scaling
- atlas, padding y camera snap
- ausencia de texturas sueltas y animaciones hardcodeadas

---

## FASE 8: Spec de salida

Lee `references/output-template.md` solo en esta fase y usa esa estructura para producir la spec final del pipeline.

Transicion: recomendar `$plan` para convertir el pipeline en tareas.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
