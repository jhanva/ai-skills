# Game Arch — Runtime Architecture para Godot 4

Lee este archivo solo cuando disenes el runtime principal del juego.

## Loop

Godot controla el loop externo. Distribuye responsabilidades asi:

- `_unhandled_input(event)`: input discreto
- `_physics_process(delta)`: gameplay, movimiento y fisica a tick fijo
- `_process(delta)`: visuales, UI y efectos por frame

`CharacterBody2D.velocity` se expresa en pixeles por segundo y
`move_and_slide()` aplica delta internamente; no multipliques `velocity` por
delta antes de llamarlo. Para movimiento en `_process`, cualquier desplazamiento
si debe escalarse por delta.

Activa `physics/common/physics_interpolation` cuando necesites suavizado entre
ticks. No implementes un accumulator manual sin una necesidad demostrada:
Godot ya gestiona el fixed timestep y limita pasos con
`Engine.max_physics_steps_per_frame`.

## Entidades

Prefiere composicion de escenas:

```text
CharacterBody2D (enemy.gd)
├─ AnimatedSprite2D
├─ CollisionShape2D
├─ HealthComponent
├─ Hurtbox (Area2D)
└─ AIBehavior
```

- nodos para comportamiento y estado vivo
- `Resource` para datos tuneables
- signals hacia arriba; llamadas directas hacia hijos que poseen la operacion
- grupos o IDs para discovery, no rutas fragiles como `../../Player`

Usa `RenderingServer`/`PhysicsServer2D` y arrays de datos solo si hay cientos o
miles de entidades y el profiling justifica saltarse nodos.

## State machine

Los estados pueden ser nodos hijos de un `StateMachine`. Cada estado implementa
`enter`, `exit`, `update`, `physics_update` y `handle_input`; solicita cambios
mediante una signal. Solo la state machine cambia el estado actual.

Senales de olor:

- mas de tres ramas `if state == ...`
- un estado llama directamente a un sibling
- input activo despues de `exit()`
- estado visual mezclado con resolucion deterministica de gameplay

## Scene stack

`change_scene_to_packed()` reemplaza una escena completa. Para overlays o una
batalla sobre exploracion, usa un autoload de stack que:

1. desactive `process_mode` y oculte la escena anterior
2. instancie la nueva `PackedScene`
3. haga `queue_free()` al retirar una escena
4. reactive y muestre la escena anterior al volver

`PROCESS_MODE_DISABLED` congela input, process y physics. Para overlays simples
tambien sirve pausar el tree y dar al overlay `PROCESS_MODE_ALWAYS`.

## Commands y eventos

Separa decision, resolucion logica y animacion. Un `GameCommand` (`RefCounted`)
debe exponer `can_execute(world)` y `execute(world) -> CommandResult`. El
resultado contiene eventos, animaciones y una posible transicion; esto hace
posibles tests, replay y AI sin cargar la escena visual.

Usa un event bus solo para eventos realmente globales. Para relaciones locales,
conecta signals entre owner e hijos; un autoload global para cada evento produce
signal spaghetti.
