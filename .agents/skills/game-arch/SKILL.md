---
name: game-arch
description: Diseña o valida arquitectura de juegos 2D, game loop, state machines, save system y patrones de escena. Úsala cuando el usuario pida explícitamente ayuda de arquitectura para un juego. No la uses para implementación genérica fuera de gamedev.
---

# Game Arch — Arquitectura de juegos 2D

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$game-arch`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, usa un baseline razonable y dejalo explicito; pregunta solo por decisiones que cambian framework, scope o target.
- Delega solo si el usuario pidio paralelismo o delegacion.

## Objetivo

Disenar o auditar la arquitectura de un juego 2D con foco en loop, entidades, estados, pantallas, comandos, persistencia y rendering.

## Carga just-in-time

- Lee `references/runtime-architecture.md` cuando debas definir game loop, entidades, state machine, screen stack o command/event flow.
- Lee `references/save-and-rendering.md` cuando debas definir save system, migraciones, batching o checklist de rendering.
- Lee `references/output-template.md` solo al redactar la spec o el reporte final.

## FASE 1: Reconocimiento

Si hay proyecto existente, identifica:

- framework
- loop actual
- manejo de estados
- estructura de entidades
- persistencia
- rendering y assets

Si es proyecto nuevo, fija:

- framework
- tipo de juego
- scope
- targets

## FASE 2: Runtime architecture

Define o valida:

- loop y manejo de `delta`
- fixed timestep si aplica
- modelo de entidades
- manejo de estados
- screens o scenes
- command queue y event bus

Para este bloque, lee `references/runtime-architecture.md`.

## FASE 3: Persistencia y rendering

Define o valida:

- formato de save
- reglas de serializacion
- seguridad al guardar/cargar
- rendering order
- batching
- lifecycle de assets

Para este bloque, lee `references/save-and-rendering.md`.

## FASE 4: Reporte

Si es proyecto nuevo:

- producir spec de estructura, loop, entidades, estados, save y render

Si es proyecto existente:

- producir findings con severidad `CRITICO`, `WARNING` e `INFO`

Usa `references/output-template.md` al cierre.

Transicion: recomendar `$plan` para convertir la arquitectura en tareas.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
