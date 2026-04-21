# Game Arch — Runtime Architecture

Lee este archivo solo cuando disenes el runtime principal del juego.

## Loop

Checklist minima:

- input
- update
- render
- `delta` tratado con cuidado
- fixed timestep si la logica necesita determinismo

Reglas utiles:

- no mover cosas con `speed` sin `delta`
- capear `delta` evita saltos despues de lag o pause
- separar update logico de render ayuda a mantener orden

## Entidades

Para juegos 2D de escala moderada, composicion simple suele ganar a herencia profunda.

Usa ECS completo solo si:

- hay muchas entidades
- el juego depende de iterar sistemas enteros
- el costo de complejidad se justifica

Anti-patrones:

- god entity
- `if (entity is X)` por todo el codigo
- referencias directas entre entidades
- logica pesada dentro de la entidad

## Estados y pantallas

Conviene explicitar:

- estados top-level
- overlays o menus
- lifecycle `enter/exit`
- ownership de input

Señal de olor: demasiados `if (state == X)` repartidos.

## Commands y eventos

Separar:

- decision de accion
- resolucion logica
- animacion

Esto facilita testing, replay y AI.
