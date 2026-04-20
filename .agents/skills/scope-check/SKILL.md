---
name: scope-check
description: >-
  Validar scope del proyecto de juego. Lee game concept (MVP mechanics), cuenta GDDs y
  stories (completadas vs pendientes), calcula velocity de sprints, proyecta tiempo
  restante, identifica riesgos (sistemas sin GDD, dependencies). Veredicto: ON TRACK, AT
  RISK, OVER-SCOPED. Si over-scoped, recomienda que mover de MVP a NICE. Usala cuando hay
  muchas features planeadas, el usuario dice "es mucho?", "llegamos?", "scope", o antes de
  planear un sprint. Auto-invoke si detectas que el backlog crece mas rapido que la
  velocity.
---

# Scope Check

## Uso en Codex

- Esta skill esta pensada para matching implicito y tambien para invocacion explicita con `$scope-check`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Cuando un ejemplo heredado mencione tools de Claude, aplica la traduccion de `AGENTS.md` y expresa la accion con herramientas reales de Codex (`rg`, `find`, `sed -n`, shell puntual y patch nativo).

Responder: "Vamos a llegar a completar el MVP?" Analizar features planeadas vs implementadas, velocity, proyeccion temporal, riesgos. Veredicto: ON TRACK / AT RISK / OVER-SCOPED.

## FASE 1: Leer game concept (MVP)

Leer `design/gdd/game-concept.md`. Si no existe, terminar con error.

Extraer: mecanicas MVP (contar), mecanicas NICE (contar). Crear tabla de mecanicas con columnas: nombre, tipo (MVP/NICE), stories estimadas, status (se llena en fases posteriores).

## FASE 2: Contar GDDs (sistemas disenados)

Buscar todos los GDDs en `design/gdd/`. Por cada uno: que sistema describe, completitud (tiene TODOs pendientes?).

Mapear GDDs a mecanicas MVP. Calcular coverage: `GDDs completos / mecanicas MVP * 100`.

Thresholds: 80-100% excelente, 50-79% moderado, <50% riesgo alto.

## FASE 3: Contar stories

Buscar stories en `production/stories/`. Clasificar por status (TODO/IN_PROGRESS/DONE) y sistema. Calcular completion rate: `DONE / total * 100`.

Mapear stories a mecanicas MVP para ver completion por mecanica.

## FASE 4: Calcular velocity

Buscar sprints completados en `production/sprints/`. Calcular velocity promedio (stories/sprint). Detectar tendencia (stable, increasing, decreasing — caida 30%+ es red flag).

Si no hay sprints completados: velocity default = 2 stories/sprint.

## FASE 5: Proyectar sprints restantes

```
stories_pendientes = TODO + IN_PROGRESS + (mecanicas_sin_stories * avg_stories_por_mecanica)
sprints_restantes = stories_pendientes / velocity_avg
tiempo_restante = sprints_restantes * duracion_sprint (default 2 semanas)
```

Comparar con deadline si existe en game-concept.md.

## FASE 6: Identificar riesgos

Evaluar cada riesgo con severity e impact:

1. **Sistemas sin GDD** → no se pueden crear stories (HIGH)
2. **Stories sin acceptance criteria** → ambiguedad, re-work (MEDIUM)
3. **Dependencies bloqueando progreso** → stories trabadas (MEDIUM-HIGH)
4. **Velocity decreasing** → proyeccion optimista (HIGH)
5. **Backlog creciendo mas rapido que velocity** → scope creep activo (HIGH)

## FASE 7: Veredicto

Scoring:

| Factor | Weight |
|---|---|
| Completion rate | x1 |
| GDD coverage | x1.5 |
| Sprints over deadline | x(-2) |
| HIGH risks | x(-30) cada |
| Velocity trend | x0 stable, x(-20) decreasing |

Thresholds: >0 ON TRACK, -50 a 0 AT RISK, <-50 OVER-SCOPED.

Incluir justificacion del veredicto con metricas concretas.

## FASE 8: Recomendaciones (si OVER-SCOPED)

Criterios para mover de MVP a NICE:
1. No es core gameplay loop
2. No bloquea otras features MVP
3. Alta complejidad (muchas stories)
4. Dependencies complejas

Recalcular proyeccion sin features movidas. Dar lista concreta: que mover, razon, stories afectadas, tiempo ahorrado.

## FASE 9: Output

Presentar reporte en conversacion (NO crear archivo).

Antes de redactarlo, leer `references/report-template.md` para formato, estructura del veredicto, y edge cases.
