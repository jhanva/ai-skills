---
name: game-arch
description: >
  Arquitectura de juegos: game loop, composicion, state machines,
  command queue, scene stack, save system, rendering 2D.
  Validacion de patrones para juegos 2D con Godot 4/GDScript.
  Usar cuando: se quiere disenar la arquitectura de un juego, validar patrones de gamedev, estructurar un proyecto, o el usuario dice "game loop", "state machine", "save system", "ECS".
argument-hint: "[aspecto de arquitectura a disenar o validar]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Bash(find:*)
  - Bash(wc:*)
  - WebFetch
  - WebSearch
---

# Game Arch — Arquitectura de juegos 2D

## Objetivo

Disenar o validar la arquitectura de un juego 2D, con patrones probados
para game loops, estados, entities, rendering, y persistencia.
Enfocado en Godot 4 + GDScript pero los patrones aplican a cualquier engine.

---

## FASE 1: Reconocimiento

### 1.1 Si hay proyecto existente

Escanear la estructura del proyecto:

```
1. Glob("**/*.gd") — listar scripts GDScript
2. Grep("class_name|extends|StateMachine|Component") — identificar patrones
3. Grep("_process|_physics_process|delta") — identificar game loop
4. Grep("save|load|FileAccess|JSON|ResourceSaver") — identificar persistencia
5. Leer project.godot — autoloads, physics ticks, display, input map
```

### 1.2 Si es proyecto nuevo

Definir con el usuario:

| Pregunta | Opciones |
|---|---|
| Engine | Godot 4 (recomendado); alternativas como Unity, GameMaker o LibGDX quedan fuera de esta skill |
| Tipo de juego | RPG, platformer, puzzle, strategy, hybrid |
| Scope | Prototype, vertical slice, full game |
| Target | Desktop only, desktop + mobile, multiplataforma + web |

---

## FASE 2: Game loop y delta time

### 2.1 Loop structure

Godot maneja el loop externo. Cada nodo implementa callbacks:

```gdscript
extends CharacterBody2D

@export var speed := 80.0

func _physics_process(delta: float) -> void:
    # 1. Input (polling; eventos discretos en _unhandled_input)
    var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")

    # 2. Update (logica, a tick fijo)
    velocity = direction * speed
    move_and_slide()

func _process(delta: float) -> void:
    # 3. Solo visual: animaciones, efectos, UI
    _update_animation()
```

### 2.2 Fixed timestep para logica

Godot ya trae el fixed timestep: `_physics_process` corre a tick fijo
(60/s por defecto, `physics/common/physics_ticks_per_second`).
No implementar accumulator manual — usar el reparto de callbacks:

```gdscript
# Logica de gameplay, fisica, colisiones → _physics_process (determinista)
func _physics_process(delta: float) -> void:
    _tick_combat(delta)

# Visual, animacion, camara cosmetica → _process (cada frame de render)
func _process(delta: float) -> void:
    _update_vfx(delta)
```

Para movimiento suave entre ticks fisicos, activar
`physics/common/physics_interpolation` (Godot 4.3+) en project settings.
El "spiral of death" ya esta capado por `Engine.max_physics_steps_per_frame`.

### 2.3 Reglas de delta time

| Regla | Por que |
|---|---|
| Nunca `position += speed` sin `* delta` en `_process` | Velocidad depende de FPS |
| `velocity` de CharacterBody2D va en px/s, sin `* delta` | `move_and_slide()` ya aplica delta internamente |
| Logica de gameplay en `_physics_process` | Fisica/colisiones deterministas a tick fijo |
| Visual en `_process` + physics interpolation activada | Smooth movement entre ticks fisicos |

---

## FASE 3: Entity architecture

### 3.1 Composicion sobre herencia

En Godot la composicion es nativa: nodos hijos como componentes de
comportamiento, Resources como datos. Para juegos por turnos esto es
mejor que ECS completo:

```gdscript
# NO: herencia profunda de scripts
# Entity > Character > PlayableCharacter > Warrior  (4 niveles de herencia)

# SI: escena compuesta por nodos-componente
# Enemy.tscn
#   CharacterBody2D (enemy.gd)
#     ├── AnimatedSprite2D
#     ├── CollisionShape2D
#     ├── HealthComponent      (health_component.gd)
#     ├── Hurtbox              (Area2D)
#     └── AIBehavior           (ai_behavior.gd)
```

```gdscript
# Datos como Resources (el equivalente a data classes)
class_name Stats
extends Resource

@export var max_hp: int = 10
@export var atk: int = 3
@export var def: int = 1
@export var spd: int = 5
```

```gdscript
# Componente reutilizable: se agrega como hijo a cualquier entity
class_name HealthComponent
extends Node

signal damaged(amount: int)
signal died

@export var stats: Stats

var current_hp: int

func _ready() -> void:
    current_hp = stats.max_hp

func take_damage(amount: int) -> void:
    current_hp = maxi(current_hp - amount, 0)
    damaged.emit(amount)
    if current_hp == 0:
        died.emit()
```

### 3.2 Cuando usar ECS / data-oriented

| Criterio | Composicion de nodos | Data-oriented (Servers, arrays) |
|---|---|---|
| Entities en pantalla | <100 | >100, miles |
| Tipo de juego | RPG por turnos, puzzle | Bullet hell, RTS, simulacion |
| Systems complejos | Pocos (combat, movement) | Muchos (physics, collision, particles) |
| Iteration patterns | Lookup por nodo/grupo | Iterar arrays de datos planos |

Para miles de entities, saltarse los nodos y usar `RenderingServer` /
`PhysicsServer2D` directo, con los datos en arrays planos.

### 3.3 Validacion

Verificar que NO existan estos anti-patrones:

```
ANTI-PATRON: God Node
  → Script con >10 fields propios (no componentes ni Resources)
  Solucion: extraer a nodos-componente y Resources de datos

ANTI-PATRON: Type checking
  → `if body is Warrior` para decidir comportamiento
  Solucion: grupos (`is_in_group`), senales, o componentes con polimorfismo

ANTI-PATRON: Hard node paths
  → `get_node("../../Player")` — rompe al mover la escena
  Solucion: senales hacia arriba, @export NodePath, o grupos/EntityManager;
  entre sistemas guardar EntityId, no referencias a nodos

ANTI-PATRON: Logic in Resource
  → Resource con metodos como calc_damage() que mutan estado del juego
  Solucion: logica en nodos/sistemas; Resources son datos (+ funciones puras)
```

---

## FASE 4: State machines

### 4.1 Hierarchical FSM

El juego tiene estados anidados:

```
GameState (top level)
  ├── ExploreState
  │     ├── MovingState
  │     ├── InteractingState (NPC dialog)
  │     └── MenuState (inventory, party)
  ├── BattleState
  │     ├── TurnStartState (apply effects, check win/lose)
  │     ├── SelectActionState (player input)
  │     ├── SelectTargetState (player input)
  │     ├── ExecuteActionState (apply damage, no input)
  │     ├── AnimateState (play animation, no input)
  │     └── TurnEndState (tick effects, next turn)
  ├── CutsceneState
  └── LoadingState
```

### 4.2 Implementacion

Estados como nodos hijos de un nodo StateMachine (visibles en el editor,
debuggeables en remote tree). Para FSMs pequenos tambien sirven clases
RefCounted; el contrato es el mismo:

```gdscript
class_name State
extends Node

signal transition_requested(next_state: StringName)

func enter(_previous: State) -> void: pass   # setup al entrar
func exit(_next: State) -> void: pass        # cleanup al salir
func update(_delta: float) -> void: pass             # visual por frame
func physics_update(_delta: float) -> void: pass     # logica a tick fijo
func handle_input(_event: InputEvent) -> bool:       # true = consumed
    return false
```

```gdscript
class_name StateMachine
extends Node

@export var initial_state: State

var current: State
var _stack: Array[State] = []   # para push/pop

func _ready() -> void:
    for child in get_children():
        if child is State:
            child.transition_requested.connect(_on_transition_requested)
    current = initial_state
    current.enter(null)

func _process(delta: float) -> void:
    current.update(delta)

func _physics_process(delta: float) -> void:
    current.physics_update(delta)

func _unhandled_input(event: InputEvent) -> void:
    if current.handle_input(event):
        get_viewport().set_input_as_handled()

func change_to(state: State) -> void:
    current.exit(state)
    state.enter(current)
    current = state

func push(state: State) -> void:
    _stack.push_back(current)
    change_to(state)

func pop() -> State:
    if _stack.is_empty():
        return null
    var resumed: State = _stack.pop_back()
    change_to(resumed)
    return resumed

func _on_transition_requested(next_state: StringName) -> void:
    change_to(get_node(NodePath(next_state)) as State)
```

### 4.3 Reglas

| Regla | Por que |
|---|---|
| Cada estado maneja su propio input | Evita input leaking entre estados |
| `enter()` / `exit()` son obligatorios | Cleanup de recursos, evita state leaks |
| Push/pop para overlays | Menu sobre explore, no reemplazar explore |
| Estados piden transicion via senal, no llaman al sibling | El StateMachine es el unico que cambia estados |
| No ifs encadenados para estados | Si hay >3 `if state == X`, es un FSM implicito — hacerlo explicito |

---

## FASE 5: Scene management

### 5.1 Scene stack

`get_tree().change_scene_to_packed()` sirve para reemplazos totales,
pero no da stack (menu sobre mapa, batalla sobre explore). Un autoload
`SceneStack` lo resuelve:

```gdscript
# autoload: SceneStack
extends Node

var _stack: Array[Node] = []

func push(scene: PackedScene) -> void:
    var current: Node = _stack.back() if not _stack.is_empty() else null
    if current:
        current.process_mode = Node.PROCESS_MODE_DISABLED
        if current is CanvasItem:
            current.hide()
    var instance := scene.instantiate()
    _stack.push_back(instance)
    get_tree().root.add_child(instance)

func pop() -> void:
    if _stack.is_empty():
        return
    var removed: Node = _stack.pop_back()
    removed.queue_free()
    var resumed: Node = _stack.back() if not _stack.is_empty() else null
    if resumed:
        resumed.process_mode = Node.PROCESS_MODE_INHERIT
        if resumed is CanvasItem:
            resumed.show()

func replace(scene: PackedScene) -> void:
    pop()
    push(scene)
```

`PROCESS_MODE_DISABLED` congela la escena de abajo (process, physics,
input); `hide()` la saca del render. Alternativa para overlays livianos:
`get_tree().paused = true` + overlay con `PROCESS_MODE_ALWAYS`.

### 5.2 Scene lifecycle

```
_enter_tree()       → nodo entra al arbol; hijos aun NO listos
_ready()            → hijos listos: conectar senales, iniciar musica
_process(delta)     → update visual cada frame
_physics_process()  → logica a tick fijo
_exit_tree()        → cleanup: desconectar de autoloads, detener timers
queue_free()        → liberar al final del frame (nunca free() en medio de una senal)
```

Assets: `preload()` para recursos pequenos conocidos en compile time,
`load()` para carga condicional, `ResourceLoader.load_threaded_request()`
para escenas pesadas (evita hitch de frame al cambiar de escena).

### 5.3 Validacion de liberacion

Los Resources se liberan por refcount; los nodos NO. Buscar leaks:

```
Grep("remove_child|\.free\(\)") en managers de escenas
→ nodo removido del arbol sin queue_free() = leak silencioso
→ verificar en debug con Node.print_orphan_nodes()
→ conexiones a autoloads (Events, SceneStack): desconectar en _exit_tree()
  o conectar con CONNECT_ONE_SHOT — si no, el autoload retiene callables muertos
```

---

## FASE 6: Command Queue y event bus

### 6.1 Command pattern para acciones de juego

```gdscript
class_name GameCommand
extends RefCounted

func can_execute(_world: GameWorld) -> bool:
    return true

func execute(_world: GameWorld) -> CommandResult:
    push_error("execute() no implementado")
    return CommandResult.new()
```

```gdscript
class_name CommandResult
extends RefCounted

var events: Array = []              # eventos generados
var animations: Array[StringName] = []  # animaciones a reproducir
var state_change: StringName = &""  # transicion de estado ("" = ninguna)
```

```gdscript
class_name CommandQueue
extends RefCounted

var _queue: Array[GameCommand] = []

func enqueue(command: GameCommand) -> void:
    _queue.push_back(command)

func process_next(world: GameWorld) -> CommandResult:
    if _queue.is_empty():
        return null
    var command: GameCommand = _queue.pop_front()
    if command.can_execute(world):
        return command.execute(world)
    return CommandResult.new()

func is_empty() -> bool:
    return _queue.is_empty()
```

### 6.2 Beneficios

| Beneficio | Detalle |
|---|---|
| Replay | Guardar secuencia de commands = replay de batalla |
| Undo | Para puzzles o movimiento en mapa |
| Network | Serializar commands para multiplayer futuro |
| Testing | Ejecutar commands sin UI ni animaciones (GameWorld puro, sin nodos) |
| AI | AI genera commands identicos a player |

### 6.3 Event bus (ligero)

Las senales de Godot YA son el event bus local: hijo emite, padre conecta.
Para eventos cross-sistema (combat → UI, quest → audio), un autoload
con senales tipadas:

```gdscript
# autoload: Events
extends Node

signal damage_dealt(amount: int, target_id: StringName)
signal battle_won(rewards: Dictionary)
```

```gdscript
# Uso:
Events.damage_dealt.connect(_on_damage_dealt)   # UI muestra numero de dano
Events.battle_won.connect(_on_battle_won)       # audio toca fanfare

Events.damage_dealt.emit(12, &"slime_03")
```

Regla: senal directa para acoplamiento local (componente → entity),
bus global SOLO para eventos que cruzan sistemas. Si todo pasa por el
autoload, es un singleton god-object disfrazado.

---

## FASE 7: Save system

### 7.1 Reglas de serializacion

| Regla | Por que |
|---|---|
| Guardar IDs, nunca referencias | Nodos y Resources no sobreviven deserializacion |
| Versionar el formato | `version: int` para migraciones futuras |
| No guardar estado derivado | Stats efectivos se recalculan al cargar |
| Guardar timestamps | Saber cuando se guardo, detectar corruption |
| JSON, no Resources, para saves de usuario | Un .tres/.res cargado puede incrustar scripts = ejecucion de codigo al cargar saves de terceros |

### 7.2 Save data structure

```gdscript
const CURRENT_SAVE_VERSION := 1

func build_save_data() -> Dictionary:
    return {
        "version": CURRENT_SAVE_VERSION,
        "timestamp": Time.get_unix_time_from_system(),
        "player": player.to_save_dict(),
        "party": party.map(func(c): return c.to_save_dict()),
        "inventory": inventory.to_save_list(),
        "quest_flags": quest_flags,
        "map_state": map_state.to_save_dict(),
        "playtime_ms": playtime_ms,
    }
```

```gdscript
# En cada personaje: IDs, no referencias ni Resources
func to_save_dict() -> Dictionary:
    return {
        "id": id,                        # ID, no referencia
        "level": level,
        "current_hp": current_hp,
        "current_mp": current_mp,
        "xp": xp,
        "equipment_ids": equipment_ids,  # IDs de items
        "status_effects": status_effects.map(func(s): return s.to_save_dict()),
    }
```

Las definiciones (stats base, items) viven en Resources bajo `res://` y
se resuelven por ID al cargar via `load()` / `ResourceLoader`.

### 7.3 Save/load flow

```
SAVE:
  1. Recolectar estado de todos los sistemas → Dictionary
  2. JSON.stringify(data)
  3. FileAccess.open("user://save.tmp", FileAccess.WRITE) + store_string()
  4. DirAccess.rename_absolute(tmp → save) (atomic)
  5. Verificar: releer y validar

LOAD:
  1. FileAccess.get_file_as_string("user://save.json")
  2. JSON.parse_string() → Dictionary
  3. Check version, migrar si hace falta
  4. Reconstruir game state desde IDs (definiciones via ResourceLoader)
  5. Recalcular stats derivados
```

### 7.4 Validacion

```
ANTI-PATRON: Objects in save
  → Grep("store_var|var_to_bytes_with_objects|ResourceSaver") en save system
  → store_var con full_objects y ResourceSaver permiten incrustar scripts:
    cargar un save manipulado = ejecucion de codigo arbitrario
  → Verificar que ningun valor del Dictionary sea Node, Resource o Callable

ANTI-PATRON: Save anywhere
  → Save solo en puntos seguros (no mid-battle, no mid-animation)
  → Verificar que el StateMachine esta en estado estable al guardar

ANTI-PATRON: No migration path
  → Si version != CURRENT, debe haber migrate(old) → new
  → Cada campo nuevo necesita default value al leer el Dictionary
```

---

## FASE 8: Rendering y batching

### 8.1 Batching

Godot batcha draw calls 2D automaticamente. No hay batch manual — el
trabajo es NO romper el batching:

```
- Sprites que comparten textura se dibujan en un draw call
  → empaquetar en sprite sheets y recortar con AtlasTexture / region_rect
- Cambiar material/shader entre sprites rompe el batch
  → compartir materiales; variar color con modulate, no con material nuevo
- TileMapLayer (Godot 4.3+; TileMap en 4.0-4.2) ya batcha por atlas
```

### 8.2 Render order

```gdscript
# Top-down: Y-sort nativo, no ordenar a mano.
# En el contenedor de entities (Node2D) y en el TileMapLayer de props:
#   y_sort_enabled = true
# Hijos se dibujan por Y global: menor Y = mas atras.

# Layers: z_index para capas dentro del mundo
ground_layer.z_index = 0
entity_layer.z_index = 1
overhead_layer.z_index = 2

# UI en CanvasLayer separado: ignora la camara, siempre encima
# HUD.tscn → CanvasLayer (layer = 10) → Control
```

### 8.3 Camera

Camera2D nativa. Follow simple: hacerla hija del player con smoothing:

```
Player (CharacterBody2D)
  └── Camera2D
        position_smoothing_enabled = true
        position_smoothing_speed = 5.0
        limit_left/top/right/bottom = bordes del mapa
```

Follow manual (camara independiente, para cutscenes o lookahead):

```gdscript
extends Camera2D

@export var target: Node2D
@export var lerp_speed := 5.0

func _physics_process(delta: float) -> void:
    if target:
        global_position = global_position.lerp(target.global_position, lerp_speed * delta)
```

### 8.4 Validacion de rendering

```
ANTI-PATRON: Instanciar nodos cada frame
  → instantiate() + add_child() por bullet/particula = spikes de GC y arbol
  Solucion: object pooling, o GPUParticles2D para efectos

ANTI-PATRON: Texturas sueltas por sprite
  → Cada textura unica = texture swap = draw call extra
  Solucion: sprite sheets compartidos + AtlasTexture

ANTI-PATRON: Material unico por instancia
  → Duplicar ShaderMaterial por sprite rompe el batching
  Solucion: material compartido; variaciones via modulate o parametros del atlas

ANTI-PATRON: Filtro linear en pixel art
  → Pixel art se ve borroso con linear filtering
  Solucion: project setting rendering/textures/canvas_textures/default_texture_filter = Nearest
```

---

## FASE 9: Reporte

### 9.1 Si es proyecto nuevo

Producir spec con:

1. **Project structure:** carpetas (`scenes/`, `scripts/`, `resources/`, `assets/`) y responsabilidades
2. **Game loop:** reparto `_process` vs `_physics_process`, physics ticks, interpolation
3. **Entity model:** composicion de nodos, componentes y Resources identificados
4. **State machine:** diagrama de estados con transiciones
5. **Scene stack:** escenas del juego con lifecycle y autoloads necesarios
6. **Command system:** commands identificados con serialize format
7. **Save system:** save data structure con version
8. **Render pipeline:** y-sort, z_index/CanvasLayer, camara, texture filter

### 9.2 Si es proyecto existente

Producir reporte con:

| Severidad | Significado |
|---|---|
| CRITICO | Bug activo o crash (node leak, senal a callable muerto, state corruption) |
| WARNING | Funcionara pero causara problemas al escalar |
| INFO | Mejora recomendada, no urgente |

Transicion: "Usa `/plan` para convertir esta arquitectura en tareas."

Argumento recibido: $ARGUMENTS
