---
name: scene-design
description: >-
  Define scene design para entities (player, enemies, UI): node tree hierarchy, signals,
  scripts con responsabilidades, y data flow. Lee GDD del sistema, define estructura de
  nodos Godot (CharacterBody2D, AnimatedSprite2D, CollisionShape2D, etc), y genera
  design/scenes/{scene-name}.md con specs completas para implementacion.
---


# Scene Design

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$scene-design`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Las referencias a `Read/Write/Edit/Grep/Glob/Bash` se traducen segun `AGENTS.md` del repo.

Define arquitectura completa de scenes en Godot: node hierarchy, signals, scripts, y data flow. Genera spec tecnica para implementar scenes con separation of concerns y testability.

## FASE 1: Leer GDD y Contexto del Sistema

**Objetivo**: Cargar informacion del sistema al que pertenece la scene.

1. Buscar documentacion del sistema relevante:
   - Para "player": `design/player-controller.md`, `design/combat-system.md`
   - Para "enemy" (slime, skeleton): `design/enemies/{name}.md`, `design/combat-system.md`
   - Para UI (inventory, pause menu): `design/ui-flow.md`, `design/{system}.md`
   - Para levels: `design/levels/{name}.md`
2. Extraer requisitos funcionales:
   - Que debe hacer esta scene (movimiento, combate, UI interactions)
   - Que inputs recibe (player input, AI, events)
   - Que outputs emite (damage, events, UI updates)
3. Identificar dependencies:
   - Autoloads que usa (EventBus, GameManager, etc.)
   - Resources que carga (sprites, sounds, data)
   - Otras scenes con las que interactua (projectiles, UI)

**Validaciones**:
- Si no hay design doc: WARNING (scene sera generica)
- Si hay multiples sistemas referenciados: Identificar responsabilidad principal

---

## FASE 2: Clasificar Scene Type

**Objetivo**: Determinar tipo de scene para aplicar template de node tree apropiado.

### Tipos de scene

| Type | Root Node | Use Case | Complexity |
|------|-----------|----------|------------|
| Character | CharacterBody2D | Player, enemies, NPCs | Medium-High |
| Projectile | Area2D | Bullets, arrows, spells | Low |
| UI Screen | Control | Menus, HUD, dialogs | Medium |
| Level | Node2D | Levels, rooms, zones | High |
| Interactable | Area2D | Chests, doors, switches | Low-Medium |
| Particle Effect | GPUParticles2D | Explosions, magic, dust | Low |

### Templates de node tree por tipo

**Character (player/enemy)**:
```
CharacterBody2D (root)
  ├─ AnimatedSprite2D (visual)
  ├─ CollisionShape2D (physics collision)
  ├─ Area2D (hurtbox, detects damage)
  │   └─ CollisionShape2D
  ├─ AudioStreamPlayer2D (SFX)
  └─ StateMachine (Node, custom logic)
```

**Projectile**:
```
Area2D (root)
  ├─ Sprite2D (visual)
  ├─ CollisionShape2D (hitbox)
  ├─ Timer (lifetime)
  └─ AudioStreamPlayer2D (SFX)
```

**UI Screen**:
```
Control (root, anchors: full rect)
  ├─ Panel (background)
  ├─ VBoxContainer (layout)
  │   ├─ Label (title)
  │   ├─ HBoxContainer (buttons)
  │   │   ├─ Button (confirm)
  │   │   └─ Button (cancel)
  │   └─ ItemList (content)
  └─ AudioStreamPlayer (UI SFX)
```

**Level**:
```
Node2D (root)
  ├─ TileMap (ground layer)
  ├─ TileMap (objects layer)
  ├─ TileMap (above layer)
  ├─ YSort (for entities con depth sorting)
  │   ├─ Player (instanced scene)
  │   ├─ Enemy1 (instanced scene)
  │   └─ Enemy2 (instanced scene)
  ├─ Camera2D (follows player)
  └─ CanvasLayer (UI overlay)
      └─ HUD (instanced scene)
```

**Interactable (chest)**:
```
Area2D (root)
  ├─ AnimatedSprite2D (closed/open states)
  ├─ CollisionShape2D (interaction trigger)
  ├─ AudioStreamPlayer2D (open sound)
  └─ Label (interaction prompt, "Press E")
```

**Decision**: Clasificar la scene y aplicar template base.

---

## FASE 3: Definir Node Tree Hierarchy

**Objetivo**: Arbol de nodos completo con tipos especificos de Godot.

### Reglas de node hierarchy

1. **Root node**: Tipo apropiado para la funcionalidad principal
   - CharacterBody2D: Entities con fisica (collision + movement)
   - Area2D: Triggers, hitboxes, hurtboxes
   - Control: UI elements
   - Node2D: Generic containers, levels
2. **Visual nodes**: Children directos del root (o de YSort si hay depth)
   - Sprite2D: Static sprites
   - AnimatedSprite2D: Animated sprites (multiple states)
3. **Collision nodes**: Siempre children del physics node (CharacterBody2D, Area2D)
   - CollisionShape2D: Shape del collision (RectangleShape2D, CapsuleShape2D, etc.)
4. **Audio nodes**: Children del root o del node que lo trigger
   - AudioStreamPlayer2D: Spatial audio (footsteps, attacks)
   - AudioStreamPlayer: Non-spatial (UI, music)
5. **Logic nodes**: Custom nodes (Node type) para state machines, AI, etc.

### Ejemplo: Player Scene

```
Player (CharacterBody2D)
  ├─ AnimatedSprite2D
  │   name: Sprite
  │   sprite_frames: res://assets/sprites/player.tres
  │   animation: "idle"
  ├─ CollisionShape2D
  │   name: BodyCollision
  │   shape: CapsuleShape2D (width: 12, height: 16)
  │   position: (0, 4)
  ├─ Area2D
  │   name: Hurtbox
  │   collision_layer: 2 (player hurtbox)
  │   collision_mask: 4 (enemy attacks)
  │   ├─ CollisionShape2D
  │       shape: RectangleShape2D (16x20)
  ├─ Area2D
  │   name: AttackHitbox
  │   collision_layer: 8 (player attacks)
  │   collision_mask: 16 (enemy hurtbox)
  │   monitoring: false (activado solo durante attack animation)
  │   ├─ CollisionShape2D
  │       shape: RectangleShape2D (20x12)
  │       position: (16, 0)  # Offset hacia derecha
  ├─ AudioStreamPlayer2D
  │   name: SFXPlayer
  │   bus: "Player SFX"
  ├─ Node
  │   name: StateMachine
  │   script: res://src/core/state_machine.gd
  │   ├─ Node (IdleState)
  │   ├─ Node (MoveState)
  │   ├─ Node (AttackState)
  │   └─ Node (HurtState)
  └─ Marker2D
      name: SpawnPoint
      position: (0, -8)  # Para spawn de VFX (dust, magic)
```

### Tabla de nodos

| Node Name | Type | Purpose | Script | Properties |
|-----------|------|---------|--------|------------|
| Player | CharacterBody2D | Root, physics body | player.gd | motion_mode=grounded |
| Sprite | AnimatedSprite2D | Visual representation | - | sprite_frames, animation |
| BodyCollision | CollisionShape2D | Physics collision | - | shape=CapsuleShape2D |
| Hurtbox | Area2D | Detects incoming damage | hurtbox.gd | collision_layer=2, mask=4 |
| AttackHitbox | Area2D | Deals damage to enemies | attack_hitbox.gd | monitoring=false initially |
| SFXPlayer | AudioStreamPlayer2D | Play attack/hurt sounds | - | bus="Player SFX" |
| StateMachine | Node | Manages player states | state_machine.gd | - |
| IdleState | Node | Idle behavior | idle_state.gd | - |
| MoveState | Node | Movement behavior | move_state.gd | - |
| AttackState | Node | Attack behavior | attack_state.gd | - |
| HurtState | Node | Hurt/invincibility | hurt_state.gd | - |

**Output**: Node tree completo + tabla de nodos con types y properties.

---

## FASE 4: Definir Signals

**Objetivo**: Signals que emite la scene y connections internas.

### Tipos de signals

**Emitted by scene** (hacia afuera):
- Events importantes que otros systems necesitan conocer
- Ej: `health_changed`, `died`, `attack_performed`

**Internal signals** (dentro de la scene):
- Communication entre child nodes
- Ej: `animation_finished`, `area_entered`, `timeout`

### Tabla de signals

| Signal | Emitted By | Parameters | Connected To | When | Purpose |
|--------|------------|------------|--------------|------|---------|
| health_changed | Player (script) | current: int, max: int | EventBus.health_changed | HP modified | Update HUD |
| died | Player (script) | - | EventBus.player_died | HP <= 0 | Trigger game over |
| attack_performed | Player (script) | damage: int | - | Attack input | Animation trigger |
| hurt | Hurtbox | damage: int | Player._on_hurt() | Area entered | Take damage |
| hit_enemy | AttackHitbox | enemy: Node | Player._on_hit_enemy() | Area entered | Deal damage |
| animation_finished | Sprite | - | StateMachine | Animation done | State transition |
| sfx_trigger | StateMachine | sfx_name: String | Player._play_sfx() | State enter | Play sound |

### Signal definitions en script

```gdscript
# player.gd
extends CharacterBody2D

signal health_changed(current: int, max: int)
signal died()
signal attack_performed(damage: int)

var health: int = 100:
    set(value):
        health = clamp(value, 0, max_health)
        health_changed.emit(health, max_health)
        if health <= 0:
            died.emit()
```

### Signal connections

**Setup en _ready()**:
```gdscript
func _ready():
    # Connect internal signals
    $Hurtbox.area_entered.connect(_on_hurtbox_area_entered)
    $AttackHitbox.area_entered.connect(_on_attack_hitbox_area_entered)
    $Sprite.animation_finished.connect(_on_animation_finished)
    
    # Connect to EventBus
    health_changed.connect(EventBus.health_changed.emit)
    died.connect(EventBus.player_died.emit)
```

**Output**: Tabla de signals + code snippets de definitions y connections.

---

## FASE 5: Definir Scripts y Responsabilidades

**Objetivo**: Scripts que se attachan a nodes, con single responsibility.

### Reglas de scripts

1. **1 script = 1 concern**: No mezclar input handling + animation + combat en un script
2. **Root script**: Coordina child scripts, no implementa toda la logica
3. **Component scripts**: Hurtbox, hitbox, state machine son components reutilizables
4. **Avoid God Object**: Si script tiene >300 lineas, refactorizar en components

### Tabla de scripts

| Script | Node | Responsibility | Dependencies | LOC Estimate |
|--------|------|----------------|--------------|--------------|
| player.gd | Player | Coordinate components, handle input, manage stats | StateMachine, EventBus | 100-150 |
| state_machine.gd | StateMachine | Manage state transitions, update current state | States (children) | 50-80 |
| idle_state.gd | IdleState | Idle behavior (play animation, check for input) | Player | 30-50 |
| move_state.gd | MoveState | Movement logic (input -> velocity) | Player | 50-80 |
| attack_state.gd | AttackState | Attack sequence (animation, enable hitbox, cooldown) | Player, AttackHitbox | 60-100 |
| hurt_state.gd | HurtState | Hurt reaction (invincibility, knockback) | Player | 40-60 |
| hurtbox.gd | Hurtbox | Detect incoming damage, emit signal | - | 20-30 |
| attack_hitbox.gd | AttackHitbox | Deal damage to overlapping enemies | - | 30-50 |

### Script templates

**player.gd** (root script):
```gdscript
extends CharacterBody2D

signal health_changed(current: int, max: int)
signal died()

@export var max_health: int = 100
@export var speed: float = 120.0

var health: int = max_health:
    set(value):
        health = clamp(value, 0, max_health)
        health_changed.emit(health, max_health)
        if health <= 0:
            _die()

@onready var sprite = $Sprite
@onready var state_machine = $StateMachine
@onready var sfx_player = $SFXPlayer

func _ready():
    # Connect signals
    $Hurtbox.hurt.connect(_on_hurt)
    health_changed.connect(EventBus.health_changed.emit)

func _physics_process(delta):
    move_and_slide()

func _on_hurt(damage: int):
    health -= damage
    state_machine.transition_to("Hurt")

func _die():
    died.emit()
    queue_free()

func play_sfx(sfx_name: String):
    var sfx = load("res://assets/audio/sfx/player/" + sfx_name + ".wav")
    sfx_player.stream = sfx
    sfx_player.play()
```

**state_machine.gd** (reusable component):
```gdscript
extends Node

@export var initial_state: NodePath

var current_state: Node
var states: Dictionary = {}

func _ready():
    for child in get_children():
        states[child.name] = child
        child.state_machine = self  # Pass reference
    
    current_state = get_node(initial_state)
    current_state.enter()

func _process(delta):
    if current_state.has_method("update"):
        current_state.update(delta)

func _physics_process(delta):
    if current_state.has_method("physics_update"):
        current_state.physics_update(delta)

func transition_to(state_name: String):
    if not states.has(state_name):
        return
    
    current_state.exit()
    current_state = states[state_name]
    current_state.enter()
```

**move_state.gd** (state example):
```gdscript
extends Node

var player: CharacterBody2D
var state_machine: Node

func _ready():
    player = get_parent().get_parent()  # StateMachine -> Player

func enter():
    player.sprite.play("walk")

func physics_update(delta):
    var input_vector = Vector2(
        Input.get_axis("move_left", "move_right"),
        Input.get_axis("move_up", "move_down")
    )
    
    if input_vector.length() == 0:
        state_machine.transition_to("IdleState")
        return
    
    player.velocity = input_vector.normalized() * player.speed
    
    # Flip sprite
    if input_vector.x != 0:
        player.sprite.flip_h = input_vector.x < 0
    
    if Input.is_action_just_pressed("attack"):
        state_machine.transition_to("AttackState")

func exit():
    player.velocity = Vector2.ZERO
```

**hurtbox.gd** (reusable component):
```gdscript
extends Area2D

signal hurt(damage: int)

func _ready():
    area_entered.connect(_on_area_entered)

func _on_area_entered(area: Area2D):
    if area.is_in_group("enemy_attack"):
        var damage = area.get("damage")
        if damage:
            hurt.emit(damage)
```

**Output**: Tabla de scripts + code templates para los principales.

---

## FASE 6: Definir Data Flow

**Objetivo**: Documentar como fluyen los datos dentro de la scene y hacia afuera.

### Data flow diagram

```
Input (keyboard/gamepad)
  ↓
player.gd (_input, _physics_process)
  ↓
StateMachine.current_state.physics_update()
  ↓
player.velocity (modified by state)
  ↓
move_and_slide() (CharacterBody2D)
  ↓
position updated
  ↓
Sprite animation updated
  ↓
Collision detection (Hurtbox, AttackHitbox)
  ↓
Signals emitted (hurt, hit_enemy)
  ↓
player.gd (signal handlers: _on_hurt, _on_hit_enemy)
  ↓
health modified
  ↓
Signal: health_changed -> EventBus
  ↓
HUD updates (external scene)
```

### Resources cargados

| Resource Type | File Path | Loaded By | When |
|---------------|-----------|-----------|------|
| SpriteFrames | res://assets/sprites/player.tres | Sprite (property) | Scene load |
| AudioStream (attack) | res://assets/audio/sfx/player/attack_*.wav | player.gd | Attack performed |
| AudioStream (hurt) | res://assets/audio/sfx/player/hurt.wav | player.gd | Damage taken |
| PackedScene (projectile) | res://scenes/prefabs/arrow.tscn | AttackState | Attack fired |

### Events emitidos al EventBus

| Event | Parameters | Cuando | Listeners Esperados |
|-------|------------|--------|---------------------|
| EventBus.health_changed | current, max | HP change | HUD, UI |
| EventBus.player_died | - | HP <= 0 | GameManager, UI |
| EventBus.enemy_defeated | enemy_name, xp | Enemy dies | GameManager, XP system |

### External dependencies

| Dependency | Type | Usage |
|------------|------|-------|
| EventBus | Autoload | Emit player events |
| GameManager | Autoload | Check pause state |
| Input | Built-in | Read player input |

**Output**: Data flow diagram + tablas de resources, events, y dependencies.

---

## FASE 7: Generar Scene Design Document

**Objetivo**: Escribir `design/scenes/{scene-name}.md` completo.

### Template del documento

```markdown
# Player Scene Design

**Scene Path**: res://scenes/characters/player.tscn
**Root Node**: CharacterBody2D
**Purpose**: Controllable player character con movement, combat, y health system
**Date**: 2026-04-17

## Node Tree

```
Player (CharacterBody2D)
  ├─ Sprite (AnimatedSprite2D)
  ├─ BodyCollision (CollisionShape2D)
  ├─ Hurtbox (Area2D)
  │   └─ CollisionShape2D
  ├─ AttackHitbox (Area2D)
  │   └─ CollisionShape2D
  ├─ SFXPlayer (AudioStreamPlayer2D)
  └─ StateMachine (Node)
      ├─ IdleState (Node)
      ├─ MoveState (Node)
      ├─ AttackState (Node)
      └─ HurtState (Node)
```

## Nodes

| Node Name | Type | Purpose | Properties |
|-----------|------|---------|------------|
| Player | CharacterBody2D | Root physics body | motion_mode=grounded |
| Sprite | AnimatedSprite2D | Visual | sprite_frames=player.tres |
| BodyCollision | CollisionShape2D | Physics collision | shape=CapsuleShape2D(12x16) |
| Hurtbox | Area2D | Damage detection | layer=2, mask=4 |
| AttackHitbox | Area2D | Damage dealing | layer=8, mask=16, monitoring=false |
| SFXPlayer | AudioStreamPlayer2D | Audio | bus="Player SFX" |
| StateMachine | Node | State manager | script=state_machine.gd |

## Signals

| Signal | Emitted By | Parameters | Connected To | Purpose |
|--------|------------|------------|--------------|---------|
| health_changed | Player | current, max | EventBus | Update HUD |
| died | Player | - | EventBus | Trigger game over |
| hurt | Hurtbox | damage | Player._on_hurt() | Take damage |
| hit_enemy | AttackHitbox | enemy | Player._on_hit_enemy() | Deal damage |

## Scripts

| Script | Node | Responsibility | LOC |
|--------|------|----------------|-----|
| player.gd | Player | Coordinate, stats, input | 120 |
| state_machine.gd | StateMachine | State transitions | 60 |
| idle_state.gd | IdleState | Idle behavior | 40 |
| move_state.gd | MoveState | Movement logic | 70 |
| attack_state.gd | AttackState | Attack sequence | 80 |
| hurt_state.gd | HurtState | Hurt reaction | 50 |
| hurtbox.gd | Hurtbox | Damage detection | 25 |
| attack_hitbox.gd | AttackHitbox | Damage dealing | 35 |

**Total LOC**: ~480

## Data Flow

1. Input (keyboard/gamepad) -> player.gd
2. StateMachine updates current_state
3. State modifies player.velocity
4. move_and_slide() updates position
5. Collision detection triggers signals
6. player.gd handles signals, modifies health
7. health_changed -> EventBus -> HUD

## Resources

| Type | Path | Usage |
|------|------|-------|
| SpriteFrames | res://assets/sprites/player.tres | Sprite animations |
| AudioStream | res://assets/audio/sfx/player/*.wav | Attack/hurt sounds |

## External Dependencies

- EventBus (autoload): Emit health_changed, died
- Input (built-in): Read move_*, attack actions

## Implementation Checklist

- [ ] Create scene: res://scenes/characters/player.tscn
- [ ] Add CharacterBody2D root node
- [ ] Add AnimatedSprite2D con player.tres
- [ ] Add CollisionShape2D (CapsuleShape2D 12x16)
- [ ] Add Hurtbox Area2D con collision layer/mask
- [ ] Add AttackHitbox Area2D con collision layer/mask
- [ ] Add AudioStreamPlayer2D (bus: Player SFX)
- [ ] Create state_machine.gd en src/core/
- [ ] Create player states en src/gameplay/player/
- [ ] Attach player.gd script to root
- [ ] Connect signals (Hurtbox.hurt, AttackHitbox.hit_enemy)
- [ ] Test movement input
- [ ] Test attack sequence
- [ ] Test damage/hurt state
- [ ] Test death sequence

## Testing Notes

**Movement**:
- WASD input -> velocity change
- Diagonal movement normalized
- Sprite flips horizontally con direction

**Combat**:
- Attack input -> AttackState
- AttackHitbox enabled during animation frames 4-5
- Hit detection emits hit_enemy signal
- Damage applied to enemy

**Health**:
- Hurtbox collision -> hurt signal
- Health decremented, clamped to 0
- health_changed signal -> EventBus
- HP <= 0 -> died signal -> queue_free()
```

**Accion**: Escribir archivo completo con datos de todas las fases.

---

## FASE 8: Validaciones Finales

**Checklist**:

- [ ] Node tree tiene <= 15 nodes (si excede, considerar split en subscenes)
- [ ] Cada node tiene purpose claro
- [ ] Scripts tienen single responsibility (LOC < 200 por script)
- [ ] Signals tienen type hints en parameters
- [ ] Data flow es unidireccional (no circular dependencies)
- [ ] Resources paths son validos
- [ ] External dependencies estan listadas
- [ ] Document incluye implementation checklist

**Warnings**:
- Si total LOC > 800: Scene muy compleja, considerar refactorizar
- Si scripts > 10: Muchos scripts, validar si todos son necesarios
- Si signals > 10: Muchas signals, simplificar communication

**Output final**: Path absoluto del archivo generado.

---

## Transicion al Siguiente Paso

Una vez completado el scene design:

1. **Siguiente**: Implementar scene en Godot siguiendo el checklist
2. **O**: `/tdd` para implementar con tests (state machine, hurtbox/hitbox logic)
3. **Despues**: Integrar scene en test level para validar gameplay
4. **Finalmente**: Refinar (balance stats, tune animations, polish SFX)

**Entregable**: `design/scenes/{scene-name}.md` con arquitectura completa de la scene.
