---
name: image-pipeline
description: Diseña arquitecturas de pipelines de procesamiento de imágenes, etapas, buffers, errores y caching. Úsala cuando el usuario pida explícitamente estructurar un pipeline de imagen multi-paso. No la uses para fixes pequeños sin trabajo de arquitectura.
---

# Image Pipeline — Diseno de pipelines de procesamiento de imagen

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$image-pipeline`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, asume un pipeline baseline y dejalo explicito; pregunta solo por restricciones que cambian la arquitectura.
- Delega solo si el usuario pidio paralelismo o delegacion.

## Objetivo

Disenar un pipeline de imagen multi-paso con stages claros, limites de memoria, modelo de concurrencia, politica de errores y estrategia de cache. El entregable debe quedar listo para `$plan`.

## Carga just-in-time

- Lee `references/memory-and-concurrency.md` cuando debas estimar memoria, elegir `Flow`/workers/chunks o definir guards.
- Lee `references/progress-errors-cache.md` cuando debas definir progreso, cancelacion, cleanup, fail-fast o persistencia incremental.

## FASE 1: Mapear el pipeline

Define cada stage con esta estructura:

```text
[Nombre] -> input -> operacion -> output -> puede fallar? -> cancelable?
```

Para cada stage, clasificalo como:

- IO-bound
- CPU-bound
- memory-bound
- UI-bound

## FASE 2: Fijar restricciones

Antes de elegir arquitectura, deja claros:

- volumen esperado
- tamano por item
- latencia total aceptable
- memoria maxima razonable
- tolerancia a fallos por item

Si hay bitmaps grandes, matrices de similitud o batches amplios, carga `references/memory-and-concurrency.md`.

## FASE 3: Elegir el modelo de ejecucion

Decide si el pipeline debe ser:

- secuencial
- por lotes
- `Flow` con backpressure
- workers dedicados
- hibrido IO + CPU

Justifica la eleccion con:

- tipo de stages
- riesgo de OOM
- necesidad de throughput
- facilidad de cancelacion y observabilidad

## FASE 4: Definir operacion segura

Define:

- progreso observable por fase
- checkpoints de cancelacion
- cleanup en cancel
- politica de errores por stage
- threshold entre best-effort y fail-fast
- cache e invalidacion

Para esto, lee `references/progress-errors-cache.md`.

## FASE 5: Spec de salida

El documento final debe incluir:

1. diagrama o tabla de stages
2. presupuesto de memoria y guards
3. modelo de concurrencia y dispatcher por tipo de trabajo
4. progreso, cancelacion y cleanup
5. estrategia de errores y retries
6. cache, invalidacion e incremental processing
7. mapeo a capas de arquitectura
8. targets de performance

Transicion: recomendar `$plan` para convertir el pipeline en tareas de implementacion.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
