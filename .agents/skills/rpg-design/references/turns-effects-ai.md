# RPG Design — Turns, Effects, and AI

Lee este archivo solo cuando definas resolucion tactica.

## Modelos de turnos

Opciones comunes:

- round-robin
- speed-based / CTB
- ATB
- timeline visible

La eleccion debe justificar:

- legibilidad para el jugador
- profundidad tactica
- costo de implementacion

## Action model

Conviene explicitar categorias como:

- `ATTACK`
- `SKILL`
- `ITEM`
- `DEFEND`
- `FLEE`

Separar resolucion logica de animacion suele simplificar pruebas y depuracion.

## Status effects

Piensa los efectos como hooks:

- on apply
- on turn start
- on turn end
- on damage dealt
- on damage received
- on remove

Define tambien:

- duracion
- stacking
- conflictos entre buffs y debuffs

## Enemy AI

Patron comun:

- pesos base
- ajustes por contexto
- reglas anti-frustracion

Anti-frustracion minima:

- no repetir el mismo skill demasiadas veces seguidas
- no bloquear permanentemente al jugador
- si el boss tiene un ataque fuerte, dar telegraph o pista
