---
name: sprint
description: >-
  Planificacion de sprint para desarrollo de juegos 2D pixel art en Godot 4. Lee el game
  concept, GDDs existentes, y sprint anterior para seleccionar 3-5 stories estimadas y con
  acceptance criteria claros. Output: production/sprints/sprint-{N}.md con sprint goal,
  stories seleccionadas, capacity, y rollover.
---

# Sprint Planning

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$sprint`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Cuando un ejemplo heredado mencione tools de Claude, aplica la traduccion de `AGENTS.md` y expresa la accion con herramientas reales de Codex (`rg`, `find`, `sed -n`, shell puntual y patch nativo).

Convertir backlog en sprint ejecutable de 1-2 semanas. Output: `production/sprints/sprint-{N}.md`.

## FASE 1: Contexto

Leer `design/gdd/game-concept.md` para MVP mechanics y scope. Buscar GDDs en `design/gdd/` para sistemas y dependencies. Crear tabla: `sistema → GDD completo? → features restantes → prioridad`.

## FASE 2: Sprint anterior

Si existe `production/sprints/sprint-{N-1}.md`: extraer stories completadas, pendientes, velocity (S/M/L completados). Rollover: stories con Status != DONE pasan automaticamente.

Si sprint 1: velocity default = 2S + 1M por semana, sin rollover.

## FASE 3: Stories candidatas

Buscar stories en `production/stories/`. Filtrar: excluir DONE, incluir rollover + nuevas.

Tabla: `ID → story → system → size → dependencies → priority`.

## FASE 4: Estimar stories

| Size | Tiempo | Descripcion |
|------|--------|-------------|
| S | 1-2h | 1-2 archivos, logica simple, sin dependencies |
| M | 3-5h | 3-5 archivos, logica moderada, 1-2 dependencies |
| L | 6-10h | 6+ archivos, logica compleja, multiples dependencies |

Si story es L: sugerir dividir en sub-stories M/S.

Forzar L si: 6+ archivos nuevos, integra 3+ sistemas, requiere assets inexistentes, toca Godot internals.

## FASE 5: Seleccionar stories

Capacity (2 semanas): 8S + 4M (ajustar por velocity real si hay sprints anteriores).

Prioridad: 1) rollover (forzado), 2) dependencies de stories en progreso, 3) MVP mechanics, 4) nice-to-have.

Max 5 stories (focus). Validar que dependencies esten completadas o incluidas en este sprint.

## FASE 6: Acceptance criteria

Por cada story: 3-7 criteria verificables ejecutando el juego, con valores concretos.

Detectar criteria vagos ("funciona bien", "se ve bien") y reemplazar con concretos.

## FASE 7: Output

Escribir `production/sprints/sprint-{N}.md` con: sprint goal (1 frase), stories tabla, acceptance criteria por story, capacity tracking, rollover, dependencies, notes.

## Edge cases

- **Sin game-concept.md**: error, crear concepto primero
- **Sin stories**: error, usar `$story` para crearlas
- **Capacity overflow por rollover**: warning, sugerir mover stories a backlog
- **Dependencies circulares**: error, sugerir romper ciclo
