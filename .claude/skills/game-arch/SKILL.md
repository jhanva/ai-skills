---
name: game-arch
description: >
  Arquitectura de juegos: game loop, composicion, state machines,
  command queue, scene stack, save system, sprite batching.
  Validacion de patrones para juegos 2D con LibGDX/Kotlin.
when_to_use: >
  Cuando el usuario quiere disenar la arquitectura de un juego,
  validar patrones de gamedev, o estructurar un proyecto de juego.
  Tambien cuando dice "game-arch", "game architecture", "game loop",
  "state machine", "scene management", "save system", "ECS".
argument-hint: "[aspecto de arquitectura a disenar o validar]"
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

# Game Arch — Arquitectura de juegos 2D

## Objetivo

Disenar o validar la arquitectura de un juego 2D, con patrones probados
para game loops, estados, entities, rendering, y persistencia.
Enfocado en LibGDX + Kotlin pero los patrones aplican a cualquier framework.

---

## FASE 1: Reconocimiento

### 1.1 Si hay proyecto existente

Escanear la estructura del proyecto:

```
1. Glob("**/*.kt") — listar archivos Kotlin
2. Grep("Screen|Stage|State|Entity|Component") — identificar patrones
3. Grep("render|update|draw|delta") — identificar game loop
4. Grep("save|load|serialize|Json") — identificar persistencia
5. Verificar build.gradle para dependencias (LibGDX, ktx, etc.)
```

### 1.2 Si es proyecto nuevo

Definir con el usuario:

| Pregunta | Opciones |
|---|---|
| Framework | LibGDX (recomendado), Korge, engine propio |
| Tipo de juego | RPG, platformer, puzzle, strategy, hybrid |
| Scope | Prototype, vertical slice, full game |
| Target | Android only, Android + desktop, multiplataforma |

---

## FASE 2: Game loop y delta time

### 2.1 Loop structure

LibGDX maneja el loop externo. El juego implementa `render(delta)`:

```kotlin
class GameScreen : Screen {
    override fun render(delta: Float) {
        // 1. Input
        handleInput()

        // 2. Update (logica, frame-independent)
        update(delta)

        // 3. Render
        batch.begin()
        draw(batch)
        batch.end()
    }
}
```

### 2.2 Fixed timestep para logica

La logica de juego debe correr a timestep fijo para determinismo:

```kotlin
private val FIXED_STEP = 1f / 60f  // 60 ticks/segundo
private var accumulator = 0f

fun update(delta: Float) {
    accumulator += minOf(delta, 0.25f)  // cap para evitar spiral of death
    while (accumulator >= FIXED_STEP) {
        fixedUpdate(FIXED_STEP)
        accumulator -= FIXED_STEP
    }
    // alpha para interpolacion de render (smooth movement)
    val alpha = accumulator / FIXED_STEP
    interpolateRender(alpha)
}
```

### 2.3 Reglas de delta time

| Regla | Por que |
|---|---|
| Nunca `position += speed` sin `* delta` | Velocidad depende de FPS |
| Cap delta a 0.25s | Evita teleport despues de pause/lag |
| Logica en fixed step | Fisica/colisiones deterministas |
| Render puede interpolar | Smooth visual entre fixed steps |

---

## FASE 3: Entity architecture

### 3.1 Composicion sobre herencia

Para juegos por turnos, composicion simple es mejor que ECS completo:

```kotlin
// NO: herencia profunda
abstract class Entity
  abstract class Character : Entity()
    abstract class PlayableCharacter : Character()
      class Warrior : PlayableCharacter()   // 4 niveles de herencia

// SI: composicion con interfaces
class Entity(val id: EntityId) {
    private val components = mutableMapOf<KClass<*>, Any>()

    fun <T : Any> add(component: T) {
        components[component::class] = component
    }

    inline fun <reified T : Any> get(): T? =
        components[T::class] as? T

    inline fun <reified T : Any> has(): Boolean =
        components.containsKey(T::class)
}

// Componentes como data classes
data class Position(var x: Float, var y: Float)
data class Stats(var hp: Int, var atk: Int, var def: Int, var spd: Int)
data class Sprite(val region: TextureRegion, var animState: String)
data class Combatant(var isAlive: Boolean = true, var turnReady: Boolean = false)
data class AIBehavior(val weights: Map<String, Int>)
```

### 3.2 Cuando usar ECS completo

| Criterio | Composicion simple | ECS (Ashley, Artemis) |
|---|---|---|
| Entities en pantalla | <100 | >100, miles |
| Tipo de juego | RPG por turnos, puzzle | Bullet hell, RTS, simulacion |
| Systems complejos | Pocos (combat, movement) | Muchos (physics, collision, particles) |
| Iteration patterns | Lookup by ID | Iterate all with Component X |

### 3.3 Validacion

Verificar que NO existan estos anti-patrones:

```
ANTI-PATRON: God Entity
  → Clase con >10 fields propios (no componentes)
  Solucion: extraer a componentes

ANTI-PATRON: Type checking
  → `if (entity is Warrior)` para decidir comportamiento
  Solucion: polimorfismo via componentes o strategy pattern

ANTI-PATRON: Entity references
  → Entity guarda referencia directa a otro Entity
  Solucion: guardar EntityId, resolver via EntityManager

ANTI-PATRON: Logic in Entity
  → Entity tiene metodos como calcDamage(), moveToward()
  Solucion: logica en systems/services, entities son datos
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

```kotlin
interface GameState {
    fun enter(previous: GameState?)   // setup al entrar
    fun exit(next: GameState?)        // cleanup al salir
    fun update(delta: Float)          // logica por frame
    fun render(batch: SpriteBatch)    // dibujar
    fun handleInput(input: InputEvent): Boolean  // true = consumed
}

class StateMachine {
    private var current: GameState? = null
    private val stack = ArrayDeque<GameState>()  // para push/pop

    fun changeTo(state: GameState) {
        current?.exit(state)
        state.enter(current)
        current = state
    }

    fun push(state: GameState) {
        stack.addLast(current!!)
        current?.exit(state)
        state.enter(current)
        current = state
    }

    fun pop(): GameState? {
        val resumed = stack.removeLastOrNull() ?: return null
        current?.exit(resumed)
        resumed.enter(current)
        current = resumed
        return resumed
    }
}
```

### 4.3 Reglas

| Regla | Por que |
|---|---|
| Cada estado maneja su propio input | Evita input leaking entre estados |
| `enter()` / `exit()` son obligatorios | Cleanup de recursos, evita state leaks |
| Push/pop para overlays | Menu sobre explore, no reemplazar explore |
| No ifs encadenados para estados | Si hay >3 `if (state == X)`, es un FSM implicito — hacerlo explicito |

---

## FASE 5: Scene / Screen management

### 5.1 Screen stack

```kotlin
class ScreenManager(private val game: Game) {
    private val screenStack = ArrayDeque<Screen>()

    fun push(screen: Screen) {
        screenStack.lastOrNull()?.pause()
        screenStack.addLast(screen)
        screen.show()
        game.screen = screen
    }

    fun pop(): Screen? {
        val removed = screenStack.removeLastOrNull() ?: return null
        removed.hide()
        removed.dispose()
        val resumed = screenStack.lastOrNull()
        resumed?.resume()
        game.screen = resumed
        return removed
    }

    fun replace(screen: Screen) {
        pop()
        push(screen)
    }

    fun disposeAll() {
        while (screenStack.isNotEmpty()) pop()
    }
}
```

### 5.2 Screen lifecycle

```
show()    → cargar assets, crear UI, iniciar musica
resume()  → re-activar input, reanudar logica
render()  → update + draw cada frame
pause()   → desactivar input, pausar timers
hide()    → liberar input processors
dispose() → liberar TODOS los assets (texturas, sounds, etc.)
```

### 5.3 Validacion de dispose

Buscar resource leaks:

```
Grep("Texture(|TextureAtlas(|Sound(|Music(|BitmapFont(") en cada Screen
→ cada uno debe tener un .dispose() correspondiente en dispose()
→ o estar manejado por AssetManager
```

---

## FASE 6: Command Queue y event bus

### 6.1 Command pattern para acciones de juego

```kotlin
interface GameCommand {
    fun execute(world: GameWorld): CommandResult
    fun canExecute(world: GameWorld): Boolean
}

data class CommandResult(
    val events: List<GameEvent>,      // eventos generados
    val animations: List<Animation>,  // animaciones a reproducir
    val stateChange: StateChange?     // transicion de estado
)

class CommandQueue {
    private val queue = ArrayDeque<GameCommand>()

    fun enqueue(command: GameCommand) = queue.addLast(command)

    fun processNext(world: GameWorld): CommandResult? {
        val command = queue.removeFirstOrNull() ?: return null
        return if (command.canExecute(world)) {
            command.execute(world)
        } else {
            CommandResult(emptyList(), emptyList(), null)
        }
    }

    val isEmpty: Boolean get() = queue.isEmpty()
}
```

### 6.2 Beneficios

| Beneficio | Detalle |
|---|---|
| Replay | Guardar secuencia de commands = replay de batalla |
| Undo | Para puzzles o movimiento en mapa |
| Network | Serializar commands para multiplayer futuro |
| Testing | Ejecutar commands sin UI ni animaciones |
| AI | AI genera commands identicos a player |

### 6.3 Event bus (ligero)

```kotlin
class EventBus {
    private val listeners = mutableMapOf<KClass<*>, MutableList<(Any) -> Unit>>()

    inline fun <reified T : Any> on(noinline handler: (T) -> Unit) {
        listeners.getOrPut(T::class) { mutableListOf() }
            .add { handler(it as T) }
    }

    fun emit(event: Any) {
        listeners[event::class]?.forEach { it(event) }
    }
}

// Uso:
eventBus.on<DamageDealtEvent> { e -> showDamageNumber(e.amount, e.target) }
eventBus.on<BattleWonEvent> { e -> playVictoryFanfare() }
```

---

## FASE 7: Save system

### 7.1 Reglas de serializacion

| Regla | Por que |
|---|---|
| Guardar IDs, nunca referencias | Las referencias no sobreviven deserializacion |
| Versionar el formato | `saveVersion: Int` para migraciones futuras |
| No guardar estado derivado | Stats efectivos se recalculan al cargar |
| Guardar timestamps | Saber cuando se guardo, detectar corruption |

### 7.2 Save data structure

```kotlin
@Serializable
data class SaveData(
    val version: Int = CURRENT_SAVE_VERSION,
    val timestamp: Long = System.currentTimeMillis(),
    val player: PlayerSaveData,
    val party: List<CharacterSaveData>,
    val inventory: List<ItemStack>,
    val questFlags: Map<String, Boolean>,
    val mapState: MapSaveData,
    val playtime: Long  // milliseconds
)

@Serializable
data class CharacterSaveData(
    val id: String,         // ID, no referencia
    val level: Int,
    val currentHp: Int,
    val currentMp: Int,
    val xp: Long,
    val equipmentIds: List<String>,  // IDs de items
    val statusEffects: List<StatusSaveData>
)
```

### 7.3 Save/load flow

```
SAVE:
  1. Collect state from all systems → SaveData
  2. Serialize to JSON (kotlinx.serialization)
  3. Write to temp file
  4. Rename temp → save file (atomic)
  5. Verify: read back and validate

LOAD:
  1. Read save file
  2. Check version, migrate if needed
  3. Deserialize → SaveData
  4. Rebuild game state from IDs
  5. Recalculate derived stats
```

### 7.4 Validacion

```
ANTI-PATRON: Object reference in save
  → Grep("@Transient|@JsonIgnore") en save data — no deberia haber
  → Verificar que ningun field sea Entity, Screen, o Texture

ANTI-PATRON: Save anywhere
  → Save solo en puntos seguros (no mid-battle, no mid-animation)
  → Verificar que save point esta en estado estable

ANTI-PATRON: No migration path
  → Si version != CURRENT, debe haber migrate(old) → new
  → Cada campo nuevo necesita default value
```

---

## FASE 8: Rendering y batching

### 8.1 Sprite batching

```kotlin
// UN batch por frame, NO un batch por entity
batch.begin()
for (entity in renderOrder) {
    val sprite = entity.get<Sprite>() ?: continue
    val pos = entity.get<Position>() ?: continue
    batch.draw(sprite.region, pos.x, pos.y)
}
batch.end()
```

### 8.2 Render order

```kotlin
// Para juegos top-down: ordenar por Y (menor Y = mas atras)
val renderOrder = entities
    .filter { it.has<Sprite>() && it.has<Position>() }
    .sortedByDescending { it.get<Position>()!!.y }

// Para juegos con layers: ordenar por layer, luego por Y
val renderOrder = entities
    .filter { it.has<Sprite>() }
    .sortedWith(compareBy<Entity> { it.get<RenderLayer>()?.z ?: 0 }
        .thenByDescending { it.get<Position>()?.y ?: 0f })
```

### 8.3 Camera

```kotlin
class GameCamera(viewportWidth: Float, viewportHeight: Float) {
    val camera = OrthographicCamera(viewportWidth, viewportHeight)
    val viewport = FitViewport(viewportWidth, viewportHeight, camera)

    fun follow(target: Position, delta: Float, lerp: Float = 5f) {
        camera.position.x += (target.x - camera.position.x) * lerp * delta
        camera.position.y += (target.y - camera.position.y) * lerp * delta
        camera.update()
    }

    fun resize(width: Int, height: Int) = viewport.update(width, height)
}
```

### 8.4 Validacion de rendering

```
ANTI-PATRON: Multiple batch.begin()/end() por frame
  → Cada begin/end es un flush = draw call extra
  Solucion: un solo batch, ordenar draws por textura

ANTI-PATRON: Crear SpriteBatch cada frame
  → SpriteBatch es pesado, crear una vez
  Solucion: campo de clase, dispose en Screen.dispose()

ANTI-PATRON: No usar TextureAtlas
  → Cada textura suelta = texture swap = draw call
  Solucion: empaquetar en atlas, un draw call por atlas

ANTI-PATRON: Nearest-neighbor no configurado
  → Pixel art se ve borroso con linear filtering
  Solucion: Texture.setFilter(Nearest, Nearest)
```

---

## FASE 9: Reporte

### 9.1 Si es proyecto nuevo

Producir spec con:

1. **Project structure:** carpetas y responsabilidades
2. **Game loop:** fixed step config, delta handling
3. **Entity model:** composicion o ECS, componentes identificados
4. **State machine:** diagrama de estados con transiciones
5. **Screen stack:** screens del juego con lifecycle
6. **Command system:** commands identificados con serialize format
7. **Save system:** save data structure con version
8. **Render pipeline:** batch strategy, render order, camera

### 9.2 Si es proyecto existente

Producir reporte con:

| Severidad | Significado |
|---|---|
| CRITICO | Bug activo o crash (memory leak, dispose faltante, state corruption) |
| WARNING | Funcionara pero causara problemas al escalar |
| INFO | Mejora recomendada, no urgente |

Transicion: "Usa `/plan` para convertir esta arquitectura en tareas."

## Argumento: $ARGUMENTS
