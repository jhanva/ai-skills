---
name: godot-setup
description: >
  Configura proyecto Godot 4 desde cero: detecta lenguaje (.gd vs .cs),
  define folder structure, configura autoloads (EventBus, managers), input
  actions, display settings, y export presets. Output: checklist de
  configuracion con valores concretos para project.godot y folder tree.
disable-model-invocation: true
agent: godot-architect
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Bash
---

# Godot Project Setup

Configura proyecto Godot 4 con best practices: folder structure organizada, autoloads esenciales, input map, display settings, y export presets. Genera checklist de configuracion para aplicar manualmente o via script.

## FASE 1: Detectar Proyecto Existente y Lenguaje

**Objetivo**: Identificar si hay proyecto Godot existente y que lenguaje usa.

### Deteccion de proyecto

1. Buscar archivo `project.godot` en directorio actual
2. Si existe:
   - Leer contenido para extraer config actual
   - Identificar lenguaje: buscar archivos `.gd` (GDScript) o `.cs` (C#)
3. Si no existe:
   - Preguntar al usuario que lenguaje prefiere
   - Crear estructura desde cero

### Comando de deteccion

```bash
# Buscar project.godot
find . -maxdepth 2 -name "project.godot"

# Contar archivos por lenguaje
find . -name "*.gd" | wc -l
find . -name "*.cs" | wc -l
```

**Decision**:
- Si `.gd` > 0: Proyecto usa GDScript
- Si `.cs` > 0: Proyecto usa C#
- Si ambos > 0: Proyecto mixto (WARNING: no recomendado)
- Si ninguno: Preguntar al usuario

### Lenguaje default para nuevo proyecto

**GDScript** (recomendado para principiantes gamedev):
- Pro: Sintaxis simple, integrado en editor, rapido iteration
- Con: Menos performance que C#, no statically typed (opcional typing)

**C#** (para devs con experiencia C#/Java/Kotlin):
- Pro: Statically typed, performance, familiaridad
- Con: Requiere Mono build de Godot, compilation step, menos ejemplos

**Recomendacion para usuario Android/Kotlin**: GDScript primero (curva de aprendizaje mas suave), migrar a C# cuando optimizacion sea necesaria.

**Output**: Lenguaje detectado/elegido.

---

## FASE 2: Definir Folder Structure

**Objetivo**: Estructura de directorios organizada y escalable.

### Standard folder structure

```
project_root/
├─ project.godot
├─ src/                     # Scripts
│   ├─ gameplay/            # Gameplay logic (player, enemies, items)
│   ├─ core/                # Core systems (state machine, resource pool)
│   ├─ ui/                  # UI controllers
│   └─ autoloads/           # Global singletons (EventBus, managers)
├─ scenes/                  # Scene files (.tscn)
│   ├─ levels/              # Level scenes
│   ├─ characters/          # Player, enemies, NPCs
│   ├─ ui/                  # Menus, HUD, dialogs
│   └─ prefabs/             # Reusable scene components
├─ assets/                  # Non-code assets
│   ├─ sprites/             # Sprite sheets, individual frames
│   ├─ tiles/               # Tileset textures
│   ├─ audio/               # SFX, music, ambience
│   │   ├─ sfx/
│   │   ├─ music/
│   │   └─ ambience/
│   ├─ fonts/               # TTF, OTF fonts
│   ├─ data/                # JSON, CSV, resource files
│   └─ shaders/             # Custom shaders
├─ design/                  # Design documents (opcional, si estan en repo)
│   ├─ sprites/
│   ├─ tilesets/
│   ├─ audio/
│   └─ levels/
├─ tests/                   # Unit tests (GUT framework)
└─ builds/                  # Export output (gitignored)
    ├─ windows/
    ├─ linux/
    └─ web/
```

### Reglas de organizacion

1. **src/**: Solo scripts (.gd o .cs), no scenes
2. **scenes/**: Solo scene files (.tscn), scripts asociados estan en src/
3. **assets/**: Solo assets binarios (png, ogg, ttf), no scripts
4. **design/**: Documentacion, puede estar fuera del proyecto Godot
5. **tests/**: Tests unitarios, usar GUT plugin
6. **builds/**: Export output, agregar a .gitignore

### .gitignore

```gitignore
# Godot-specific
.import/
*.import
.godot/
builds/

# Mono-specific (if using C#)
.mono/
data_*/
mono_crash.*.json
```

**Accion**: Crear directorios si no existen.

```bash
mkdir -p src/{gameplay,core,ui,autoloads}
mkdir -p scenes/{levels,characters,ui,prefabs}
mkdir -p assets/{sprites,tiles,audio/{sfx,music,ambience},fonts,data,shaders}
mkdir -p tests
mkdir -p builds
```

**Output**: Folder tree creado.

---

## FASE 3: Configurar Autoloads (Singletons)

**Objetivo**: Definir autoloads esenciales para arquitectura global.

### Autoloads recomendados

| Name | Script | Purpose | Priority |
|------|--------|---------|----------|
| EventBus | event_bus.gd | Global event system (decoupled communication) | Essential |
| GameManager | game_manager.gd | Game state (paused, score, level) | Essential |
| SaveManager | save_manager.gd | Save/load system | Important |
| AudioManager | audio_manager.gd | Music/SFX playback control | Important |
| SceneTransition | scene_transition.gd | Scene loading con transitions | Optional |

### EventBus (event_bus.gd)

**Proposito**: Comunicacion desacoplada entre nodos sin referencias directas.

```gdscript
# src/autoloads/event_bus.gd
extends Node

# Combat events
signal enemy_defeated(enemy_name: String, xp_reward: int)
signal player_hurt(damage: int, remaining_hp: int)
signal player_died()

# UI events
signal score_changed(new_score: int)
signal health_changed(current_hp: int, max_hp: int)

# Level events
signal level_completed(level_name: String)
signal checkpoint_reached(checkpoint_id: int)

# Emit example: EventBus.enemy_defeated.emit("Slime", 10)
# Connect example: EventBus.enemy_defeated.connect(_on_enemy_defeated)
```

**Best practices**:
- Agrupar signals por categoria (combat, UI, level)
- Nombres descriptivos (subject_verb, ej: player_hurt, score_changed)
- Type hints en signal parameters

### GameManager (game_manager.gd)

**Proposito**: Estado global del juego (score, level, paused).

```gdscript
# src/autoloads/game_manager.gd
extends Node

var score: int = 0
var current_level: String = ""
var is_paused: bool = false

func add_score(points: int) -> void:
    score += points
    EventBus.score_changed.emit(score)

func pause_game() -> void:
    is_paused = true
    get_tree().paused = true

func resume_game() -> void:
    is_paused = false
    get_tree().paused = false

func reset_game() -> void:
    score = 0
    current_level = ""
    is_paused = false
```

### SaveManager (save_manager.gd)

**Proposito**: Persistencia de datos (JSON file save/load).

```gdscript
# src/autoloads/save_manager.gd
extends Node

const SAVE_PATH = "user://savegame.json"

func save_game(data: Dictionary) -> void:
    var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file:
        file.store_string(JSON.stringify(data))
        file.close()

func load_game() -> Dictionary:
    if not FileAccess.file_exists(SAVE_PATH):
        return {}
    
    var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
    if file:
        var json_string = file.get_as_text()
        file.close()
        return JSON.parse_string(json_string)
    return {}
```

### AudioManager (audio_manager.gd)

**Proposito**: Control centralizado de musica y SFX.

```gdscript
# src/autoloads/audio_manager.gd
extends Node

@onready var music_player = AudioStreamPlayer.new()
@onready var sfx_player = AudioStreamPlayer.new()

func _ready():
    add_child(music_player)
    add_child(sfx_player)
    music_player.bus = "Music"
    sfx_player.bus = "SFX"

func play_music(track_name: String) -> void:
    var track = load("res://assets/audio/music/" + track_name + ".ogg")
    if music_player.stream != track:
        music_player.stream = track
        music_player.play()

func play_sfx(sfx_name: String) -> void:
    var sfx = load("res://assets/audio/sfx/" + sfx_name + ".wav")
    sfx_player.stream = sfx
    sfx_player.play()
```

### Configuracion en project.godot

**Manual** (via Godot Editor):
- Project > Project Settings > Autoload
- Add: Path = `res://src/autoloads/event_bus.gd`, Name = `EventBus`, Enable = Yes

**Automatico** (via script edit):

```ini
[autoload]

EventBus="*res://src/autoloads/event_bus.gd"
GameManager="*res://src/autoloads/game_manager.gd"
SaveManager="*res://src/autoloads/save_manager.gd"
AudioManager="*res://src/autoloads/audio_manager.gd"
```

**Output**: Tabla de autoloads + scripts base + configuracion project.godot.

---

## FASE 4: Configurar Input Actions

**Objetivo**: Input map con soporte keyboard + gamepad.

### Input actions por categoria

**UI Navigation**:
- `ui_accept`: Enter, Space, Gamepad A
- `ui_cancel`: Escape, Gamepad B
- `ui_up`: Arrow Up, Gamepad D-Pad Up
- `ui_down`: Arrow Down, Gamepad D-Pad Down
- `ui_left`: Arrow Left, Gamepad D-Pad Left
- `ui_right`: Arrow Right, Gamepad D-Pad Right

**Player Movement** (top-down):
- `move_up`: W, Arrow Up, Gamepad Left Stick Up
- `move_down`: S, Arrow Down, Gamepad Left Stick Down
- `move_left`: A, Arrow Left, Gamepad Left Stick Left
- `move_right`: D, Arrow Right, Gamepad Left Stick Right

**Player Movement** (platformer):
- `move_left`: A, Arrow Left, Gamepad D-Pad Left
- `move_right`: D, Arrow Right, Gamepad D-Pad Right
- `jump`: Space, Gamepad A

**Player Actions**:
- `attack`: Mouse Left Click, J, Gamepad X
- `interact`: E, Gamepad A
- `dodge`: Shift, Gamepad B
- `inventory`: I, Tab, Gamepad Y

**System**:
- `pause`: Escape, Gamepad Start
- `fullscreen`: F11

### Tabla de input actions

| Action | Keys | Gamepad | Deadzone | Type |
|--------|------|---------|----------|------|
| ui_accept | Enter, Space | Button 0 (A) | - | Digital |
| ui_cancel | Escape | Button 1 (B) | - | Digital |
| move_up | W, Up Arrow | Left Stick Up | 0.2 | Analog/Digital |
| move_down | S, Down Arrow | Left Stick Down | 0.2 | Analog/Digital |
| move_left | A, Left Arrow | Left Stick Left | 0.2 | Analog/Digital |
| move_right | D, Right Arrow | Left Stick Right | 0.2 | Analog/Digital |
| attack | Mouse Button 1, J | Button 2 (X) | - | Digital |
| interact | E | Button 0 (A) | - | Digital |
| pause | Escape | Button 6 (Start) | - | Digital |

### Configuracion en project.godot

```ini
[input]

move_up={
"deadzone": 0.2,
"events": [
  Object(InputEventKey, "keycode": 87, "pressed": false),  # W
  Object(InputEventKey, "keycode": 4194320, "pressed": false),  # Up Arrow
  Object(InputEventJoypadMotion, "axis": 1, "axis_value": -1.0)  # Left Stick Up
]
}

move_down={
"deadzone": 0.2,
"events": [
  Object(InputEventKey, "keycode": 83, "pressed": false),  # S
  Object(InputEventKey, "keycode": 4194322, "pressed": false),  # Down Arrow
  Object(InputEventJoypadMotion, "axis": 1, "axis_value": 1.0)  # Left Stick Down
]
}

move_left={
"deadzone": 0.2,
"events": [
  Object(InputEventKey, "keycode": 65, "pressed": false),  # A
  Object(InputEventKey, "keycode": 4194319, "pressed": false),  # Left Arrow
  Object(InputEventJoypadMotion, "axis": 0, "axis_value": -1.0)  # Left Stick Left
]
}

move_right={
"deadzone": 0.2,
"events": [
  Object(InputEventKey, "keycode": 68, "pressed": false),  # D
  Object(InputEventKey, "keycode": 4194321, "pressed": false),  # Right Arrow
  Object(InputEventJoypadMotion, "axis": 0, "axis_value": 1.0)  # Left Stick Right
]
}

attack={
"events": [
  Object(InputEventMouseButton, "button_index": 1),  # Left Click
  Object(InputEventKey, "keycode": 74, "pressed": false),  # J
  Object(InputEventJoypadButton, "button_index": 2)  # X
]
}

interact={
"events": [
  Object(InputEventKey, "keycode": 69, "pressed": false),  # E
  Object(InputEventJoypadButton, "button_index": 0)  # A
]
}

pause={
"events": [
  Object(InputEventKey, "keycode": 4194305, "pressed": false),  # Escape
  Object(InputEventJoypadButton, "button_index": 6)  # Start
]
}
```

**Usage en scripts**:

```gdscript
func _process(delta):
    var velocity = Vector2.ZERO
    
    if Input.is_action_pressed("move_up"):
        velocity.y -= 1
    if Input.is_action_pressed("move_down"):
        velocity.y += 1
    if Input.is_action_pressed("move_left"):
        velocity.x -= 1
    if Input.is_action_pressed("move_right"):
        velocity.x += 1
    
    velocity = velocity.normalized() * speed
    move_and_slide(velocity)

func _input(event):
    if event.is_action_pressed("attack"):
        _perform_attack()
```

**Output**: Tabla de actions + configuracion project.godot.

---

## FASE 5: Display Settings

**Objetivo**: Configuracion de viewport, resolution, y scaling.

### Display settings para pixel art

| Setting | Value | Reason |
|---------|-------|--------|
| Window Width | 1280 | Base resolution (16:9 aspect ratio) |
| Window Height | 720 | HD resolution |
| Viewport Width | 320 | Internal resolution (4x scale) |
| Viewport Height | 180 | Internal resolution (4x scale) |
| Stretch Mode | canvas_items | Scales UI and sprites correctly |
| Stretch Aspect | keep | Maintains aspect ratio, letterbox if needed |
| Stretch Scale | integer | Pixel-perfect scaling (no blur) |

### Configuracion en project.godot

```ini
[display]

window/size/viewport_width=320
window/size/viewport_height=180
window/size/window_width_override=1280
window/size/window_height_override=720
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"
window/stretch/scale_mode="integer"

[rendering]

textures/canvas_textures/default_texture_filter=0  # Nearest neighbor (no blur)
2d/snapping/use_gpu_pixel_snap=true  # Pixel snap enabled
```

### Aspect ratio y scaling

**Internal resolution** (320x180):
- Ratio: 16:9
- Scale: 4x -> 1280x720 (HD)
- Scale: 5x -> 1600x900
- Scale: 6x -> 1920x1080 (Full HD)

**Alternatives**:
- 160x144 (Game Boy resolution, 10:9 ratio)
- 256x224 (SNES resolution, ~8:7 ratio)
- 400x240 (GBA resolution, 5:3 ratio)

**Recomendacion**: 320x180 para juegos modernos con pixel art (16:9 es standard).

### Pixel snap

**GPU pixel snap**: Enabled
- Alinea sprites al pixel grid
- Evita sub-pixel rendering (no blur/jitter)

**Tile snap**: Enabled para TileMaps
- Asegura que tiles esten alineados perfectamente

**Output**: Tabla de display settings + configuracion project.godot.

---

## FASE 6: Export Presets

**Objetivo**: Configurar export templates para multiples plataformas.

### Plataformas recomendadas

| Platform | Binary Name | Features | Notes |
|----------|-------------|----------|-------|
| Windows Desktop | game.exe | DirectX/Vulkan, gamepad | Mas facil para testing |
| Linux/X11 | game.x86_64 | Vulkan, gamepad | Universal compatibility |
| HTML5 (Web) | index.html | WebGL 2, touch/mouse | Itch.io, Newgrounds |
| macOS | game.app | Metal, gamepad | Requiere certificado (opcional) |

### Export preset: Windows

**Settings**:
- Export Path: `builds/windows/game.exe`
- Runnable: Yes
- Dedicated Server: No
- Texture Format: VRAM Compressed
- Binary Format: 64-bit
- Embed PCK: Yes (single .exe file)

**Custom Resources**: Excluir archivos innecesarios
- Excluir: `design/*`, `tests/*`, `*.md`, `.git`

### Export preset: HTML5

**Settings**:
- Export Path: `builds/web/index.html`
- Texture Format: VRAM Compressed
- Canvas Resize Policy: Adaptive
- Export Type: Regular
- Vram Texture Compression: For Desktop
- HTML Shell: Default
- Head Include: (custom meta tags si es necesario)

**Limitaciones**:
- No multithreading (single-threaded)
- No file system access (usar localStorage)
- Audio puede requerir user interaction para reproducir

### Configuracion en export_presets.cfg

```ini
[preset.0]

name="Windows Desktop"
platform="Windows Desktop"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter="design/*, tests/*, *.md, .git*"
export_path="builds/windows/game.exe"
encryption_include_filters=""
encryption_exclude_filters=""
script_encryption_key=""

[preset.0.options]

binary_format/64_bits=true
texture_format/bptc=true
texture_format/s3tc=true
texture_format/etc=false
texture_format/etc2=false
binary_format/embed_pck=true

[preset.1]

name="HTML5"
platform="HTML5"
runnable=true
export_filter="all_resources"
exclude_filter="design/*, tests/*, *.md, .git*"
export_path="builds/web/index.html"

[preset.1.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
```

**Output**: Export presets configurados + export_presets.cfg.

---

## FASE 7: Generar Checklist de Configuracion

**Objetivo**: Documento con checklist de todas las configuraciones a aplicar.

### Template del checklist

```markdown
# Godot Project Setup Checklist

**Project**: [nombre del juego]
**Engine**: Godot 4.x
**Language**: GDScript
**Date**: 2026-04-17

## 1. Folder Structure

- [ ] Crear directorios: src/{gameplay,core,ui,autoloads}
- [ ] Crear directorios: scenes/{levels,characters,ui,prefabs}
- [ ] Crear directorios: assets/{sprites,tiles,audio,fonts,data,shaders}
- [ ] Crear directorios: tests, builds
- [ ] Crear .gitignore con reglas de Godot

## 2. Autoloads

- [ ] Crear src/autoloads/event_bus.gd
- [ ] Crear src/autoloads/game_manager.gd
- [ ] Crear src/autoloads/save_manager.gd
- [ ] Crear src/autoloads/audio_manager.gd
- [ ] Configurar autoloads en Project Settings

## 3. Input Actions

- [ ] Configurar move_up, move_down, move_left, move_right
- [ ] Configurar attack, interact, pause
- [ ] Configurar ui_accept, ui_cancel (navigation)
- [ ] Testear keyboard input
- [ ] Testear gamepad input

## 4. Display Settings

- [ ] Set viewport size: 320x180
- [ ] Set window size: 1280x720
- [ ] Set stretch mode: canvas_items
- [ ] Set stretch aspect: keep
- [ ] Set stretch scale: integer
- [ ] Enable pixel snap (GPU)
- [ ] Set texture filter: Nearest neighbor

## 5. Audio Buses

- [ ] Crear bus: SFX (child de Master)
- [ ] Crear bus: Music (child de Master)
- [ ] Set volumes: SFX -3dB, Music -6dB
- [ ] Agregar Limiter effect a Master bus

## 6. Export Presets

- [ ] Configurar Windows Desktop export
- [ ] Configurar HTML5 export (opcional)
- [ ] Set exclude filters (design/*, tests/*, .git*)
- [ ] Testear build Windows
- [ ] Testear build HTML5

## 7. Testing

- [ ] Crear scene de testing: scenes/test_scene.tscn
- [ ] Testear input actions (movement, attack)
- [ ] Testear EventBus (emit y connect signals)
- [ ] Testear SaveManager (save y load)
- [ ] Testear AudioManager (play music y SFX)
- [ ] Testear export build (run .exe)

## Configuration Files

**project.godot** (key sections):

```ini
[autoload]
EventBus="*res://src/autoloads/event_bus.gd"
GameManager="*res://src/autoloads/game_manager.gd"
SaveManager="*res://src/autoloads/save_manager.gd"
AudioManager="*res://src/autoloads/audio_manager.gd"

[display]
window/size/viewport_width=320
window/size/viewport_height=180
window/size/window_width_override=1280
window/size/window_height_override=720
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"
window/stretch/scale_mode="integer"

[input]
move_up={...}
move_down={...}
attack={...}
interact={...}

[rendering]
textures/canvas_textures/default_texture_filter=0
2d/snapping/use_gpu_pixel_snap=true
```

**.gitignore**:

```gitignore
.import/
*.import
.godot/
builds/
.mono/
```

## Next Steps

1. Import assets (sprites, tiles, audio) a assets/
2. Crear player scene en scenes/characters/player.tscn
3. Crear test level en scenes/levels/test_level.tscn
4. Implementar player movement usando input actions
5. Testear game loop basico
```

**Accion**: Escribir checklist completo.

---

## FASE 8: Validaciones Finales

**Checklist**:

- [ ] Folder structure cubre todos los asset types
- [ ] Autoloads cubren funcionalidad core (events, game state, save, audio)
- [ ] Input actions cubren movimiento + acciones principales
- [ ] Display settings son apropiados para pixel art
- [ ] Export presets estan configurados para al menos 1 plataforma
- [ ] Checklist es accionable (no pasos ambiguos)

**Warnings**:
- Si autoloads > 6: Demasiados singletons, considerar refactorizar
- Si input actions > 20: Excesivo, priorizar
- Si export presets > 4: Multiples plataformas aumentan complejidad de testing

**Output final**: Path absoluto del checklist generado.

---

## Transicion al Siguiente Paso

Una vez completada la configuracion:

1. **Siguiente**: Importar assets (`/sprite-spec`, `/tileset-spec`, `/sound-brief`)
2. **O**: Crear primera scene (player, test level)
3. **Despues**: `/scene-design player` para diseñar player scene
4. **Finalmente**: Implementar gameplay loop basico

**Entregable**: Checklist de configuracion completo en conversacion o archivo markdown.
