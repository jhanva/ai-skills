---
name: scope-check
description: >
  Validar scope del proyecto de juego. Lee game concept (MVP mechanics), cuenta GDDs
  y stories (completadas vs pendientes), calcula velocity de sprints, proyecta tiempo
  restante, identifica riesgos (sistemas sin GDD, dependencies). Veredicto: ON TRACK,
  AT RISK, OVER-SCOPED. Si over-scoped, recomienda que mover de MVP a NICE.
when_to_use: >
  Cuando hay muchas features planeadas, el usuario dice "es mucho?", "llegamos?",
  "scope", o antes de planear un sprint. Auto-invoke si detectas que el backlog crece
  mas rapido que la velocity.
argument-hint: "[no arguments]"
allowed-tools:
  - Read
  - Grep
  - Glob
agent: producer
---

# Scope Check

Agent que valida si el scope del proyecto de juego es alcanzable dado el tiempo,
recursos, y velocity actual. Diseñado para solo dev principiante en gamedev con
experiencia en Android/Kotlin.

## Objetivo

Responder la pregunta: "Vamos a llegar a completar el MVP?"

Output:
- Conteo de features: planeadas vs implementadas
- Velocity: stories completadas por sprint
- Proyeccion: sprints restantes para completar MVP
- Riesgos: sistemas sin diseño, dependencies bloqueando progreso
- Veredicto: ON TRACK, AT RISK, OVER-SCOPED
- Si over-scoped: recomendaciones concretas de que mover a backlog

## Entrada

```
/scope-check
```

Sin argumentos. Auto-invocable cuando detectas señales de scope creep.

## FASE 1: Leer game concept (MVP)

### 1.1 Localizar game concept

Buscar `design/game-concept.md`:

```
Read: design/game-concept.md
```

Si no existe:
- Error: "No se encontro design/game-concept.md. Debes definir el MVP primero."
- Terminar

### 1.2 Contar mecanicas MVP

Buscar seccion "## MVP Features" o "## Core Mechanics":

Ejemplo:
```markdown
## MVP Features

1. Player movement (4-directional)
2. Combat (turn-based, damage formula)
3. Inventory (pickup, equip, use items)
4. Enemy AI (patrol, chase, attack)
5. Level progression (XP, level up, stat increase)
6. Save/Load system
```

Contar: **6 mecanicas MVP**

### 1.3 Identificar NICE features

Buscar seccion "## Nice-to-Have" o "## Post-MVP":

Ejemplo:
```markdown
## Nice-to-Have

1. Crafting system
2. Multiplayer
3. Quest system
4. Dialogue trees
5. Day/night cycle
```

Contar: **5 features NICE**

### 1.4 Crear tabla de mecanicas

| # | Mecanica | Type | Estimated stories | Status |
|---|----------|------|-------------------|--------|
| 1 | Player movement | MVP | 2 | ? |
| 2 | Combat | MVP | 5 | ? |
| 3 | Inventory | MVP | 4 | ? |
| 4 | Enemy AI | MVP | 3 | ? |
| 5 | Level progression | MVP | 3 | ? |
| 6 | Save/Load | MVP | 2 | ? |
| **Total MVP** | | | **19** | |
| 7 | Crafting | NICE | 6 | ? |
| 8 | Multiplayer | NICE | 15 | ? |

Status se llena en FASE 3.

## FASE 2: Contar GDDs (sistemas diseñados)

### 2.1 Buscar todos los GDDs

```
Glob: design/gdd/**/*.md
```

Por cada archivo encontrado, leer:
- Titulo (que sistema describe)
- Completitud (tiene todas las secciones? hay TODOs?)

### 2.2 Mapear GDDs a mecanicas MVP

Ejemplo:
```
Encontrados:
- design/gdd/combat.md (completo)
- design/gdd/inventory.md (completo)
- design/gdd/movement.md (completo)
- design/gdd/enemy-ai.md (parcial, tiene TODOs)
```

Actualizar tabla de FASE 1:

| Mecanica | GDD Status | Blocker? |
|----------|------------|----------|
| Player movement | COMPLETE (movement.md) | No |
| Combat | COMPLETE (combat.md) | No |
| Inventory | COMPLETE (inventory.md) | No |
| Enemy AI | PARTIAL (enemy-ai.md tiene TODOs) | Si |
| Level progression | MISSING | Si |
| Save/Load | MISSING | Si |

### 2.3 Calcular coverage

```
GDD coverage = (GDDs completos / Mecanicas MVP) * 100
Ejemplo: (3 / 6) * 100 = 50%
```

Thresholds:
- **80-100%:** Excelente, diseño casi completo
- **50-79%:** Moderado, algunos sistemas sin diseñar
- **< 50%:** Riesgo alto, mas de la mitad sin diseño

## FASE 3: Contar stories (trabajo implementable)

### 3.1 Buscar todas las stories

```
Glob: production/stories/**/*.md
```

Por cada story, leer:
- Status: TODO, IN_PROGRESS, DONE
- Size: S, M, L
- Sistema (del filename: {system}-{feature}.md)

### 3.2 Clasificar stories por status

Crear tabla:

| Sistema | Total stories | DONE | IN_PROGRESS | TODO | Total size (DONE) |
|---------|---------------|------|-------------|------|-------------------|
| combat | 5 | 2 | 1 | 2 | 1S + 1M |
| inventory | 4 | 0 | 1 | 3 | 0 |
| movement | 2 | 2 | 0 | 0 | 2S |
| enemy-ai | 3 | 0 | 0 | 3 | 0 |
| **Total** | **14** | **4** | **2** | **8** | **3S + 1M** |

### 3.3 Calcular completion rate

```
Completion = (DONE / Total stories) * 100
Ejemplo: (4 / 14) * 100 = 28.5%
```

### 3.4 Mapear stories a mecanicas MVP

Actualizar tabla de FASE 1 con status:

| Mecanica | Estimated stories | Actual stories | Completion |
|----------|-------------------|----------------|------------|
| Player movement | 2 | 2 | 100% (2/2 DONE) |
| Combat | 5 | 5 | 40% (2/5 DONE) |
| Inventory | 4 | 4 | 0% (0/4 DONE) |
| Enemy AI | 3 | 3 | 0% (0/3 DONE) |
| Level progression | 3 | 0 | 0% (sin stories) |
| Save/Load | 2 | 0 | 0% (sin stories) |

## FASE 4: Calcular velocity (sprints history)

### 4.1 Buscar sprint history

```
Glob: production/sprints/**/*.md
```

Ordenar por numero de sprint (sprint-1.md, sprint-2.md, ...).

### 4.2 Calcular velocity por sprint

Por cada sprint completado (status no es current), leer:
- Stories planeadas
- Stories completadas (Status: DONE)
- Size de stories completadas

Crear tabla:

| Sprint | Stories planeadas | Stories completadas | Size completada | Velocity (stories) | Velocity (size) |
|--------|-------------------|---------------------|-----------------|-------------------|-----------------|
| 1 | 3 | 2 | 2S + 1M | 2 | 2S + 1M |
| 2 | 4 | 3 | 3S | 3 | 3S |
| 3 | 3 | 3 | 1S + 2M | 3 | 1S + 2M |
| **Avg** | | **2.67** | | **2.67** | **2S + 1.3M** |

### 4.3 Detectar tendencias

Velocity increasing?
- Sprint 1: 2 stories
- Sprint 2: 3 stories
- Sprint 3: 3 stories
- Tendencia: **STABLE** (no crecimiento significativo)

Velocity decreasing?
- Si velocity cae 30%+ entre sprints: **RED FLAG**
- Ejemplo: Sprint 1: 3 stories, Sprint 2: 2 stories, Sprint 3: 1 story → DECREASING

### 4.4 Velocity default si no hay sprints

Si no existen sprints completados:
- Warning: "No hay sprints completados. Usando velocity default."
- Velocity default: 2 stories/sprint (1S + 1M)

## FASE 5: Proyectar sprints restantes

### 5.1 Calcular trabajo restante

```
Stories pendientes = TODO + IN_PROGRESS + (Mecanicas sin stories * avg_stories_per_mecanica)

Ejemplo:
TODO = 8
IN_PROGRESS = 2
Mecanicas sin stories = 2 (level-progression, save-load)
Avg stories per mecanica = 14 stories / 4 mecanicas = 3.5

Stories pendientes = 8 + 2 + (2 * 3.5) = 17
```

### 5.2 Proyectar sprints

```
Sprints restantes = Stories pendientes / Velocity avg

Ejemplo: 17 / 2.67 = 6.4 sprints
```

Si duracion de sprint es conocida (default 2 semanas):
```
Tiempo restante = 6.4 sprints * 2 semanas = 12.8 semanas (~3 meses)
```

### 5.3 Comparar con deadline

Si existe deadline en game-concept.md:
- Leer "## Timeline" o "## Deadline"
- Comparar tiempo restante vs deadline

Ejemplo:
```
Deadline: 8 semanas (2 meses)
Tiempo restante proyectado: 12.8 semanas

Deficit: 4.8 semanas (60% sobre deadline)
```

## FASE 6: Identificar riesgos

### 6.1 Riesgo: Sistemas sin GDD

De FASE 2, listar mecanicas MVP sin GDD completo:

| Mecanica | Riesgo | Impact |
|----------|--------|--------|
| Level progression | MISSING GDD | HIGH (sin diseño, no se puede crear stories) |
| Save/Load | MISSING GDD | HIGH |
| Enemy AI | PARTIAL GDD (TODOs) | MEDIUM (diseño incompleto) |

### 6.2 Riesgo: Stories sin acceptance criteria

Buscar stories con acceptance criteria vacios o < 3 items:

```
Grep: "## Acceptance Criteria" en production/stories/
Contar lineas en la tabla
```

Si story tiene < 3 criteria:
- Riesgo: ambiguedad en que significa "done"
- Impact: MEDIUM (puede causar re-work)

### 6.3 Riesgo: Dependencies bloqueando progreso

De las stories en TODO/IN_PROGRESS, leer dependencies:

Buscar dependencies con Status: TODO o MISSING

Ejemplo:
```
Story: combat/damage-formula
Dependency: stats/base-stats (Status: TODO)

Blocker: combat/damage-formula no puede completarse hasta que stats/base-stats exista
```

Contar stories bloqueadas por dependencies faltantes.

### 6.4 Riesgo: Velocity decreasing

De FASE 4, si velocity esta cayendo:
- Riesgo: burnout, complejidad creciente, o scope creep
- Impact: HIGH (proyeccion optimista, tiempo real sera mayor)

### 6.5 Riesgo: Backlog creciendo mas rapido que velocity

```
Stories agregadas en ultimos 2 sprints: 10
Stories completadas en ultimos 2 sprints: 5

Backlog growth rate = (10 - 5) / 2 = +2.5 stories/sprint
```

Si backlog growth > 0:
- Riesgo: scope creep activo
- Impact: HIGH (nunca terminaras)

### 6.6 Tabla de riesgos

| # | Riesgo | Severity | Impact | Mitigacion |
|---|--------|----------|--------|------------|
| 1 | 2 mecanicas sin GDD | HIGH | No se pueden crear stories | Completar GDDs con /brainstorm |
| 2 | 3 stories bloqueadas por dependencies | MEDIUM | Bloquean progreso de otras features | Resolver dependencies primero |
| 3 | Velocity decreasing (3→2→1) | HIGH | Proyeccion muy optimista | Re-estimar con velocity conservadora |
| 4 | Backlog creciendo +2.5/sprint | HIGH | Scope creep activo | Congelar nuevas features |

## FASE 7: Veredicto

### 7.1 Calcular score

Factores:

| Factor | Value | Weight | Score |
|--------|-------|--------|-------|
| Completion rate | 28.5% | x1 | 28.5 |
| GDD coverage | 50% | x1.5 | 75 |
| Sprints over deadline | +60% | x(-2) | -120 |
| HIGH risks count | 3 | x(-30) | -90 |
| Velocity trend | STABLE | x0 | 0 |
| **Total** | | | **-106.5** |

### 7.2 Thresholds

| Score | Veredicto |
|-------|-----------|
| > 0 | ON TRACK |
| -50 to 0 | AT RISK |
| < -50 | OVER-SCOPED |

Este proyecto: **-106.5** → **OVER-SCOPED**

### 7.3 Justificacion del veredicto

**ON TRACK:**
- Completion rate > 60%
- GDD coverage > 80%
- Dentro del deadline
- 0-1 riesgos HIGH
- Velocity stable o increasing

**AT RISK:**
- Completion rate 30-60%
- GDD coverage 50-80%
- 10-30% sobre deadline
- 1-2 riesgos HIGH
- Velocity stable pero ajustado

**OVER-SCOPED:**
- Completion rate < 30%
- GDD coverage < 50%
- 30%+ sobre deadline
- 3+ riesgos HIGH
- Velocity decreasing o backlog creciendo

## FASE 8: Recomendaciones (si OVER-SCOPED)

### 8.1 Identificar features para mover a NICE

Criterios para mover de MVP a NICE:
1. No es core gameplay loop
2. No bloquea otras features MVP
3. Alta complejidad (muchas stories)
4. Dependencies complejas

Ejemplo:

| Mecanica actual | Stories | Complexity | Blocker? | Mover a NICE? |
|-----------------|---------|------------|----------|---------------|
| Level progression | 3 | MEDIUM | No (solo afecta stats) | **SI** |
| Save/Load | 2 | HIGH | No (QoL feature) | **SI** |
| Enemy AI | 3 | MEDIUM | Si (combate necesita enemigos) | **NO** |

### 8.2 Recalcular proyeccion sin features movidas

```
Stories pendientes originales: 17
Stories de level-progression: 3
Stories de save/load: 2

Stories pendientes ajustadas: 17 - 3 - 2 = 12

Sprints restantes: 12 / 2.67 = 4.5 sprints
Tiempo restante: 4.5 * 2 = 9 semanas
```

Comparar con deadline:
```
Deadline: 8 semanas
Nuevo tiempo restante: 9 semanas
Deficit: 1 semana (12.5% sobre deadline)
```

Nuevo veredicto: **AT RISK** (mucho mejor que OVER-SCOPED)

### 8.3 Lista concreta de cambios

```markdown
## Recomendaciones para alcanzar MVP

### Mover a Nice-to-Have (Post-MVP)

1. **Level progression**
   - Razon: No es critico para primer playable
   - Stories afectadas: 3 (level-up, stat-increase, xp-formula)
   - Tiempo ahorrado: ~1 sprint

2. **Save/Load system**
   - Razon: Playtest no requiere persistencia
   - Stories afectadas: 2 (save-data, load-data)
   - Tiempo ahorrado: ~0.75 sprint

### Mantener en MVP

- Player movement (core)
- Combat (core gameplay loop)
- Inventory (necesario para items/equip)
- Enemy AI (necesario para combate)

### Proximos pasos

1. Actualizar design/game-concept.md: mover features a Nice-to-Have
2. Mover stories de production/stories/ a production/stories/backlog/
3. Re-estimar sprint actual con scope reducido
4. Completar GDDs faltantes antes de crear mas stories
```

## FASE 9: Output en conversacion

### 9.1 Formato de reporte

```markdown
# Scope Check Report

**Fecha:** {fecha-actual}
**Proyecto:** {nombre del juego del game-concept.md}

## Summary

| Metric | Value |
|--------|-------|
| MVP Mechanics | 6 |
| GDD Coverage | 50% (3/6 completos) |
| Total Stories | 14 |
| Completion Rate | 28.5% (4/14 DONE) |
| Velocity (avg) | 2.67 stories/sprint |
| Sprints Completados | 3 |
| Sprints Restantes | 6.4 (~13 semanas) |
| Deadline | 8 semanas |
| Deficit | +5 semanas (60% over) |

## Veredicto: OVER-SCOPED

Score: -106.5 (threshold: < -50)

## Riesgos Identificados

| # | Riesgo | Severity | Mitigacion |
|---|--------|----------|------------|
| 1 | 2 mecanicas sin GDD | HIGH | Completar con /brainstorm |
| 2 | 3 stories bloqueadas | MEDIUM | Resolver dependencies |
| 3 | 60% sobre deadline | HIGH | Reducir scope MVP |

## Recomendaciones

Mover a Nice-to-Have:
- Level progression (3 stories, ~1 sprint)
- Save/Load (2 stories, ~0.75 sprint)

Con estos cambios:
- Sprints restantes: 4.5 (~9 semanas)
- Nuevo deficit: 1 semana (12.5% over)
- Nuevo veredicto: AT RISK (aceptable)

## Proximos pasos

1. Actualizar game-concept.md (mover features)
2. Archivar stories no-MVP en production/stories/backlog/
3. Completar GDDs faltantes (enemy-ai, otros)
4. /sprint para planear siguiente sprint con scope reducido
```

No crear archivo, solo output en conversacion.

## Edge cases

### Sin sprints completados
Si no hay sprints:
- Usar velocity default (2 stories/sprint)
- Warning: "Proyeccion basada en velocity default. Ajustar despues del primer sprint."

### Sin deadline
Si game-concept.md no tiene deadline:
- Solo reportar "Sprints restantes: X"
- No calcular deficit
- Veredicto basado en completion rate y riesgos

### Proyecto muy nuevo (< 5 stories)
Si hay muy pocas stories:
- Warning: "Proyecto muy temprano para scope check preciso"
- Reportar GDD coverage y recomendar diseñar mas antes de estimar

### Velocity muy variable
Si velocity varia 50%+ entre sprints:
- Warning: "Velocity inestable. Usar sprint mas reciente como referencia."
- No promediar, usar ultimo sprint

## Output esperado

Reporte en conversacion (no archivo) de 40-80 lineas con:
- Tabla de metricas
- Veredicto (ON TRACK / AT RISK / OVER-SCOPED)
- Riesgos con severity
- Recomendaciones concretas si over-scoped

Tiempo de ejecucion: 1-2 min
