---
name: pixel-pipeline
description: >
  Pipeline de assets pixel art: sprite sheets, animaciones, tilesets,
  palette swapping, import en Godot 4, Aseprite workflow. Disenar el
  flujo completo de Aseprite a Godot para juegos 2D.
when_to_use: >
  Cuando el usuario quiere disenar el pipeline de assets para un juego
  pixel art, organizar sprites, configurar animaciones, o integrar
  tilesets. Tambien cuando dice "pixel-pipeline", "sprite sheet",
  "tileset", "palette swap", "texture atlas", "Aseprite", "pixel art",
  "animaciones de sprites".
argument-hint: "[aspecto del pipeline o problema especifico]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Bash(find *)
  - Bash(wc *)
  - WebFetch
  - WebSearch
---

# Pixel Pipeline — Pipeline de assets pixel art

## Objetivo

Disenar el flujo completo desde Aseprite hasta juego funcional en
Godot 4: resolucion, sprite sheets, animaciones, tilesets, palette
management, y organizacion e import de sheets. El output es una spec
de pipeline y convenciones lista para el equipo de arte y desarrollo.

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

Este naming permite agrupar frames por entity+animation al construir
el SpriteFrames o al slicear el sheet en Godot.

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

### 2.4 Animation controller (Godot 4)

En Godot el playback lo maneja `AnimatedSprite2D` + `SpriteFrames`.
Para mantener el sistema data-driven, construir el SpriteFrames desde
el JSON de 2.3 (regiones del sheet via AtlasTexture):

```gdscript
# src/core/animation_builder.gd
static func build_frames(sheet: Texture2D, data: Dictionary,
        regions: Dictionary) -> SpriteFrames:
    var frames := SpriteFrames.new()
    for anim_name in data:
        var anim: Dictionary = data[anim_name]
        frames.add_animation(anim_name)
        frames.set_animation_loop(anim_name, anim["loop"])
        frames.set_animation_speed(anim_name, 1.0 / anim["frameDuration"])
        for frame_name in anim["frames"]:
            var tex := AtlasTexture.new()
            tex.atlas = sheet
            tex.region = regions[frame_name]  # Rect2 del JSON de Aseprite
            frames.add_frame(anim_name, tex)
    return frames
```

```gdscript
# src/core/animation_controller.gd
class_name AnimationController
extends AnimatedSprite2D

func play_anim(anim_name: String, on_complete: Callable = Callable()) -> void:
    if animation == anim_name and is_playing():
        return
    play(anim_name)
    if on_complete.is_valid() and not sprite_frames.get_animation_loop(anim_name):
        animation_finished.connect(on_complete, CONNECT_ONE_SHOT)

var is_playing_one_shot: bool:
    get:
        return is_playing() and not sprite_frames.get_animation_loop(animation)
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

### 3.3 Integracion en Godot (TileSet + TileMapLayer)

```
Workflow:
  1. Crear tileset en Aseprite (exportar como PNG)
  2. Importar PNG en Godot y crear un TileSet resource:
     - Atlas source apuntando al PNG (tile size = grid del proyecto)
     - Physics layer para colision (polygon por tile solido)
     - Terrain sets para autotile (bitmask 4-bit o 8-bit de 3.2)
     - Custom data layers para metadata (ej: "blocked", "damage")
  3. Pintar el mapa con nodos TileMapLayer (uno por capa visual):
     - Ground     (z_index=0, siempre debajo)
     - Objects    (z_index=1, arboles, rocas)
     - Above      (z_index=2, techos, copas de arboles — sobre player)
  4. Colision: NO usar un layer invisible de tiles — la physics layer
     del TileSet colisiona automaticamente con CharacterBody2D
  5. Events (spawn, door, dialog): nodos Area2D/Marker2D en la escena
     del nivel, o custom data en tiles + query desde codigo
```

### 3.4 Walkability y pathfinding

```gdscript
@onready var ground: TileMapLayer = $Ground

func is_walkable(tile_pos: Vector2i) -> bool:
    var data: TileData = ground.get_cell_tile_data(tile_pos)
    return data != null and not data.get_custom_data("blocked")

# Pathfinding: AStarGrid2D (A* sobre grid, built-in en Godot 4)
var astar := AStarGrid2D.new()

func _setup_pathfinding() -> void:
    astar.region = ground.get_used_rect()
    astar.cell_size = Vector2(16, 16)
    astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER  # 4-way
    astar.update()
    for cell in ground.get_used_cells():
        if not is_walkable(cell):
            astar.set_point_solid(cell, true)

func find_path(start: Vector2i, end: Vector2i) -> Array[Vector2i]:
    return astar.get_id_path(start, end)
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
// palette_swap.gdshader (canvas_item shader de Godot 4)
shader_type canvas_item;

uniform sampler2D u_palette : filter_nearest;  // lookup texture (Nx filas)
uniform float u_palette_row = 0.0;             // cual paleta usar (0.0 = base)

void fragment() {
    vec4 color = texture(TEXTURE, UV);

    // Usar canal rojo como indice en la lookup texture
    float index = color.r;
    vec4 swapped = texture(u_palette, vec2(index, u_palette_row));

    COLOR = vec4(swapped.rgb, color.a);
}
```

Aplicar via ShaderMaterial en el Sprite2D/AnimatedSprite2D. Para
variantes por instancia sin duplicar material, usar
`material.set_shader_parameter("u_palette_row", row)` sobre un
material unico por variante (o instance uniforms).

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

## FASE 5: Sprite sheets e import en Godot

### 5.1 Aseprite export workflow

```
Aseprite → File → Export Sprite Sheet
  Layout: By Rows
  Sheet type: Packed (minimo espacio)
  Output file: {entity}.png
  JSON data: {entity}.json (Array format)
  Split layers: NO (composite)
  Split tags: SI (cada tag = una animacion)
```

### 5.2 Import en Godot 4 (sin packer externo)

Godot 4 NO necesita un paso de atlas packing con herramienta externa.
El editor importa los PNG directamente (genera `*.import` + cache en
`.godot/`) y el renderer 2D batchea draw calls automaticamente. La
unidad de trabajo es el sprite sheet por entity que exporta Aseprite.

```
Directorio de assets (Godot lo importa tal cual):
  assets/
    sprites/
      player.png        ← sheet exportado de Aseprite (5.1)
      player.json       ← metadata de frames (Aseprite)
      slime.png
      slime.json
    tiles/
      terrain.png
      buildings.png
    ui/
      ui.png

Como se consume cada tipo:
  Sprite sheets → SpriteFrames (AnimatedSprite2D), regiones via
                  AtlasTexture (ver 2.4)
  Tilesets      → TileSet resource con atlas source al PNG (ver 3.3)
  UI            → AtlasTexture por icono, NinePatchRect para panels

Cuando SI consolidar:
  - Cientos de PNG sueltos de 1 frame → consolidar en un sheet por
    entity (menos archivos .import, menos texture switches)
  - NO hace falta un atlas global del juego: agrupar por contexto
    (5.4) es suficiente
```

### 5.3 Import settings (pixel art)

Filtering en Godot 4 es global (project setting) con override por
nodo, NO una opcion de import por textura:

```ini
# project.godot (igual que /godot-setup y /art-bible)
[rendering]
textures/canvas_textures/default_texture_filter=0  # Nearest
2d/snap/snap_2d_transforms_to_pixel=true  # Pixel snap (Godot 4)
```

En el dock Import, por textura:

```
Compress > Mode: Lossless
Mipmaps > Generate: Off
Detect 3D: Disabled
```

| Setting | Valor | Por que |
|---|---|---|
| default_texture_filter | 0 (Nearest) | Pixel art, nunca Linear |
| Compress Mode | Lossless | Compresion VRAM (S3TC/ETC) destruye pixel art |
| Mipmaps | Off | Innecesarios en 2D, causan blur al escalar |
| Padding en sheets | 2px entre frames | Evita bleeding al recortar AtlasTexture |
| Sheet size | <= 2048x2048 | Soporte universal en mobile |

Si un nodo especifico necesita otro filtering, usar
`CanvasItem.texture_filter = TEXTURE_FILTER_NEAREST` — nunca cambiar
el default global a Linear.

### 5.4 Sheets por contexto

No consolidar TODO en un solo sheet. Separar por uso y cargar por
contexto:

```
characters.png  → player, party, NPCs (siempre cargados en explore)
enemies.png     → sprites de enemigos (cargados en batalla)
tiles/*.png     → tilesets (cargados por zona/mapa)
ui.png          → iconos, frames, fonts (siempre cargados)
effects.png     → particulas, spell effects (cargados en batalla)
```

```gdscript
# Siempre cargados: preload (resuelto en compile/parse time)
const UI_SHEET := preload("res://assets/ui/ui.png")

# Por zona/contexto: load al entrar, soltar referencias al salir
var zone_tiles: Texture2D = load("res://assets/tiles/%s.png" % zone_name)

# Zonas pesadas: carga en background sin frame hitch
ResourceLoader.load_threaded_request("res://scenes/levels/zone_2.tscn")
```

### 5.5 Memory budget

```
Sheet 2048x2048 RGBA = 16MB en VRAM
Sheet 1024x1024 RGBA = 4MB en VRAM

Budget para mobile:
  Characters: 1x 1024x1024 = 4MB
  Enemies:    1x 1024x1024 = 4MB
  Tiles:      1x 2048x2048 = 16MB (zona actual)
  UI:         1x 1024x1024 = 4MB
  Effects:    1x 512x512   = 1MB
  TOTAL: ~29MB VRAM en peak (batalla)

Regla: total sheets VRAM < 64MB en mobile
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

En Godot:
  NinePatchRect con texture = dialog_box (o region del sheet de UI)
  patch_margin_left/top/right/bottom = 3
  axis_stretch_horizontal/vertical = Stretch o Tile (segun el borde)
```

### 6.2 Pixel font

```
Opciones:
  1. Bitmap font generado con BMFont (o exportado de Aseprite)
     → Export como .fnt + .png
     → Godot lo importa directo como FontFile
     → Nearest filtering via default_texture_filter global

  2. Pixel font sprite sheet
     → Cada caracter como celda del sheet
     → En Godot: FontFile creado desde imagen (image font)
     → Alineado a grid (monospace recomendado para pixel)

Regla: tamano de font = multiplo del pixel size base
  Si pixel = 1 unit, font size = 8 o 16 (nunca 12, 14, etc.)
```

---

## FASE 7: Validacion

### 7.1 Checklist de consistencia visual

```
[ ] Todos los sprites usan la misma paleta base
[ ] Tamano de tiles consistente en todo el proyecto
[ ] No hay sprites con resolucion mezclada (16x16 junto a 24x24)
[ ] Filtering = Nearest en TODAS las texturas
[ ] Integer scaling en la camara/viewport
[ ] Outlines consistentes (todas o ninguna, mismo color)
[ ] Sombras/highlights consistentes (misma direccion de luz)
```

### 7.2 Validacion tecnica

```
[ ] Sheets por entity/contexto (no cientos de PNG de 1 frame en produccion)
[ ] Sheet size <= 2048x2048 (compatibilidad mobile)
[ ] Padding >= 2 entre frames dentro del sheet
[ ] Todos los sprites en la misma pixels-per-unit
[ ] Camera snapping a pixel grid implementado
[ ] Import: Compress Lossless + Mipmaps Off en todas las texturas
[ ] No se cargan sheets innecesarios (load por zona/contexto,
    soltar referencias al salir para que Godot libere VRAM)
```

### 7.3 Anti-patrones

```
ANTI-PATRON: Un PNG suelto por frame en produccion
  → Cientos de archivos .import, texture switches innecesarios
  → (Godot batchea draw calls, pero el desorden y los switches quedan)
  Solucion: sheet por entity + SpriteFrames/AtlasTexture

ANTI-PATRON: Linear filtering en pixel art
  → Sprites borrosos, bleeding entre frames
  Solucion: default_texture_filter=0 en project.godot, sin
  overrides Linear en texture_filter de nodos

ANTI-PATRON: Rotacion con angulos arbitrarios
  → Pixels deformados, apariencia inconsistente
  Solucion: solo 0/90/180/270, o pre-renderizar rotaciones

ANTI-PATRON: Sprites de diferente resolucion mezclados
  → Pixels de tamano visualmente diferente
  Solucion: todo a la misma base, escalar en la herramienta de arte

ANTI-PATRON: Animaciones hardcodeadas
  → Cambiar timing requiere recompilar
  Solucion: datos de animacion en JSON/XML, no en codigo

ANTI-PATRON: No camera snap
  → Sub-pixel movement causa shimmer/jitter en tiles
  Solucion: snap camera position a pixel grid
```

---

## FASE 8: Spec de salida

Producir documento con:

1. **Convenciones:** resolucion, grid, paleta, render resolution
2. **Sprite list:** tabla de entities con animaciones y frame counts
3. **Tileset plan:** tilesets necesarios, autotile type (terrain sets), TileMapLayers
4. **Sheet strategy:** sheets por contexto con memory budget
5. **Animation data format:** JSON schema para animaciones
6. **Palette system:** paleta base + variantes + shader approach
7. **Aseprite workflow:** export settings, naming convention, batch export
8. **Integration:** como se importan y cargan los assets en Godot 4
   (import settings, SpriteFrames, TileSet, code snippets)

Transicion: "Usa `/plan` para convertir este pipeline en tareas."

## Argumento: $ARGUMENTS
