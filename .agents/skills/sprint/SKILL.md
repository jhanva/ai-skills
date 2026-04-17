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
- Las referencias a `Read/Write/Edit/Grep/Glob/Bash` se traducen segun `AGENTS.md` del repo.

Agent que planifica sprints de desarrollo para juegos 2D pixel art en Godot 4.
Diseñado para solo dev principiante en gamedev con experiencia en Android/Kotlin.

## Objetivo

Convertir el backlog de stories en un sprint ejecutable de 1-2 semanas con:
- Sprint goal claro (1 frase)
- 3-5 stories seleccionadas y estimadas
- Acceptance criteria medibles por story
- Capacity tracking (S/M/L)
- Rollover de trabajo pendiente del sprint anterior

## Entrada

```
/sprint [numero]
/sprint 1
/sprint 5
```

Si no se proporciona numero, calcular automaticamente: ultimo sprint + 1

## FASE 1: Contexto del proyecto

### 1.1 Leer game concept

Leer `design/game-concept.md`:
- MVP mechanics: cuales son las mecanicas core que deben funcionar?
- Scope: que esta dentro del MVP vs NICE?
- Milestone actual: donde estamos en el desarrollo?

### 1.2 Leer GDDs existentes

Buscar todos los GDDs en `design/gdd/`:

```
Glob: design/gdd/**/*.md
```

Por cada GDD, extraer:
- Sistema diseñado
- Features implementables
- Dependencies entre sistemas

Crear tabla de sistemas:

| Sistema | GDD completo? | Features restantes | Prioridad |
|---------|---------------|-------------------|-----------|
| combat  | Si            | 3                 | High      |
| inventory | Parcial     | 7                 | Medium    |

## FASE 2: Historia del sprint anterior

Si existe `production/sprints/sprint-{N-1}.md`:

### 2.1 Leer resultados del sprint anterior

Extraer:
- Stories completadas (Status: DONE)
- Stories pendientes (Status: IN_PROGRESS, TODO)
- Velocity: cuantas S/M/L se completaron?

Calcular velocity:
- S completadas: cuantas?
- M completadas: cuantas?
- L completadas: cuantas?
- Total capacity consumida

### 2.2 Identificar rollover

Stories con Status != DONE pasan automaticamente al nuevo sprint como rollover.

Ejemplo:
```
Sprint 4 rollover:
- inventory/quick-slots (M, IN_PROGRESS)
- ui/health-bar (S, TODO)
```

Si NO hay sprint anterior:
- Es el sprint 1
- Velocity default: 2S + 1M por semana
- No hay rollover

## FASE 3: Listar stories candidatas

Buscar todas las stories en `production/stories/`:

```
Glob: production/stories/**/*.md
```

Por cada story, leer:
- Status (si existe)
- Estimacion (si existe)
- Dependencies

Filtrar:
- Excluir stories con Status: DONE
- Incluir rollover del sprint anterior
- Incluir stories nuevas sin status

Crear tabla de candidatas:

| ID | Story | System | Size | Dependencies | Priority |
|----|-------|--------|------|--------------|----------|
| story-001 | damage-formula | combat | M | - | High |
| story-002 | item-pickup | inventory | S | - | Medium |

## FASE 4: Estimar stories

Por cada story candidata SIN estimacion:

### 4.1 Reglas de estimacion

| Size | Tiempo | Descripcion | Ejemplos |
|------|--------|-------------|----------|
| S    | 1-2h   | 1-2 archivos nuevos, logica simple, sin dependencies | UI component, data model, simple script |
| M    | 3-5h   | 3-5 archivos, logica moderada, 1-2 dependencies | Combat turn, inventory slot system, state machine |
| L    | 6-10h  | 6+ archivos, logica compleja, multiples dependencies | Enemy AI, save system, level editor integration |

### 4.2 Flags de complejidad

Si una story tiene 2+ de estos flags, es L:
- Toca multiples sistemas (combat + inventory + UI)
- Requiere assets nuevos (sprites, animations, sounds)
- Integra con Godot editor (custom nodes, inspector plugins)
- Logica con edge cases complejos (pathfinding, collision)

### 4.3 Dividir stories L

Si una story es L, sugerir dividir en sub-stories M/S:

Ejemplo:
```
Original (L): enemy-ai/behavior-tree
Dividir en:
- enemy-ai/chase-player (M)
- enemy-ai/attack-range (S)
- enemy-ai/retreat-low-hp (M)
```

### 4.4 Actualizar tabla

Agregar columna Size a la tabla de candidatas.

## FASE 5: Seleccionar stories para el sprint

### 5.1 Calcular capacity disponible

Duracion del sprint (default 2 semanas):
- Capacity = 4S + 2M por semana
- 2 semanas = 8S + 4M

Ajustar por experiencia:
- Si velocity del sprint anterior < capacity default, usar velocity real
- Si es sprint 1, usar capacity default

### 5.2 Priorizar stories

Orden de prioridad:
1. Rollover del sprint anterior (siempre entra)
2. Dependencies de stories en progreso
3. MVP mechanics sin implementar (del game-concept.md)
4. Nice-to-have features

### 5.3 Seleccionar hasta llenar capacity

Algoritmo:
```
capacity_restante = capacity_total
stories_seleccionadas = []

1. Agregar rollover (forzado)
2. Mientras capacity_restante > 0:
   - Tomar siguiente story por prioridad
   - Si story.size <= capacity_restante:
       agregar a seleccionadas
       capacity_restante -= story.size
   - Si no, siguiente story

3. Limitar a max 5 stories (focus)
```

### 5.4 Validar dependencies

Por cada story seleccionada, verificar que sus dependencies esten:
- Ya completadas (Status: DONE en sprints anteriores)
- Incluidas en este sprint

Si hay dependencies faltantes:
- Advertencia al usuario
- Sugerir agregar dependency o remover story

## FASE 6: Definir acceptance criteria

Por cada story seleccionada:

### 6.1 Leer story file

Si existe `production/stories/{story}.md`, leer acceptance criteria existentes.

### 6.2 Generar criteria si faltan

Formato de acceptance criteria:

| # | Criteria | How to verify |
|---|----------|---------------|
| 1 | Player deals damage to enemy | Run combat scene, attack enemy, check enemy HP decreases |
| 2 | Damage formula uses ATK stat | Print damage calculation, verify ATK value is used |
| 3 | Critical hits deal 1.5x damage | Attack 20 times, verify ~5% crits, verify damage value |

Reglas:
- 3-7 criteria por story (no mas, no menos)
- Cada criterio es verificable ejecutando el juego
- Incluir valores esperados concretos (HP decreases, 1.5x, 5%)
- Avoid ambiguedad ("funciona bien" → "damage decreases enemy HP by ATK value")

### 6.3 Detectar criteria vagos

Flags de criteria vago:
- "funciona correctamente"
- "se ve bien"
- "no tiene bugs"
- "esta completo"

Si detectas flag vago, reemplazar con criterio concreto.

## FASE 7: Output del sprint

### 7.1 Formato del archivo

Crear `production/sprints/sprint-{N}.md`:

```markdown
# Sprint {N}

**Duracion:** {fecha-inicio} a {fecha-fin} (2 semanas)
**Sprint Goal:** {1 frase describiendo el objetivo principal}

## Stories seleccionadas

| ID | Story | System | Size | Status | Owner |
|----|-------|--------|------|--------|-------|
| story-001 | damage-formula | combat | M | TODO | dev |
| story-002 | item-pickup | inventory | S | TODO | dev |
| story-003 | health-bar | ui | S | IN_PROGRESS | dev |

## Acceptance Criteria

### story-001: damage-formula

| # | Criteria | How to verify |
|---|----------|---------------|
| 1 | Player deals damage to enemy | Run combat scene, attack enemy, check HP decreases |
| 2 | Damage uses ATK stat | Print calculation, verify ATK value used |
| 3 | Critical hits at 5% rate | Attack 20 times, ~1 crit |

### story-002: item-pickup

| # | Criteria | How to verify |
|---|----------|---------------|
| 1 | Player collides with item, item disappears | Walk over item sprite |
| 2 | Item added to inventory data | Print inventory array |
| 3 | Pickup sound plays | Listen for audio feedback |

## Capacity

| Metric | Value |
|--------|-------|
| Total stories | 3 |
| Total size | 2S + 1M |
| Capacity used | 6h (2S) + 4h (1M) = 10h |
| Capacity available | 40h (2 semanas) |
| Utilization | 25% |

## Rollover from Sprint {N-1}

| Story | Reason | Action |
|-------|--------|--------|
| story-003 (health-bar) | 80% complete, UI polish pending | Finish in first 2 days |

## Dependencies

| Story | Depends on | Status |
|-------|------------|--------|
| story-001 | combat/base-stats | DONE (Sprint 3) |

## Notes

- Focus on combat MVP this sprint
- Health bar rollover should complete early
- Item pickup is low risk, good filler story
```

### 7.2 Validar output

Checklist antes de escribir archivo:
- [ ] Sprint goal es 1 frase clara
- [ ] 3-5 stories seleccionadas
- [ ] Cada story tiene acceptance criteria (3-7 items)
- [ ] Capacity calculada correctamente
- [ ] Dependencies listadas y validadas
- [ ] Rollover documentado

## FASE 8: Transicion al usuario

Mensaje final:

```
Sprint {N} planeado: {sprint-goal}

Stories seleccionadas: {count}
Capacity: {total-size}

Proximo paso:
1. Usa `/story {system}/{feature}` para detallar cada story
2. Luego `/plan` para convertir stories en tareas de implementacion
3. Ejecuta con `/execute` (usa `/tdd` internamente)

Archivo generado: production/sprints/sprint-{N}.md
```

## Edge cases

### Sin game-concept.md
Error: "No se encontro design/game-concept.md. Debes crear el game concept primero."

### Sin GDDs
Warning: "No hay GDDs en design/gdd/. Considera usar `/brainstorm` para diseñar sistemas antes de planear sprints."

### Sin stories
Error: "No hay stories en production/stories/. Usa `/story` para crear stories primero."

### Capacity overflow
Si rollover > capacity disponible:
- Warning: "Rollover excede capacity del sprint. Considera extender duracion o renegociar scope."
- Mostrar tabla de rollover con size total
- Sugerir que stories M/L mover a backlog

### Dependencies circulares
Si story A depende de B y B depende de A:
- Error: "Dependencia circular detectada entre {A} y {B}"
- Sugerir romper ciclo dividiendo una story

## Output esperado

Archivo markdown estructurado con:
- Sprint goal (1 frase)
- Tabla de stories con status
- Acceptance criteria detallados por story
- Capacity tracking
- Rollover y dependencies

Tamaño: 100-200 lineas
Tiempo de ejecucion: 2-3 min
