# Image Pipeline — Memory and Concurrency

Lee este archivo solo cuando necesites cuantificar memoria o elegir patron de concurrencia.

## Budget rapido de memoria

Formulas utiles:

- bitmap decode: `width * height * 4`
- bitmap escalado: `targetW * targetH * 4`
- embedding: `dimension * 4`
- similarity matrix: `N * N * 4`

Reglas practicas:

- peak por item: idealmente < 50MB
- peak total: idealmente < 200MB en mobile
- si `N > 5000`, paginar o procesar incrementalmente
- si la comparacion es all-pairs y `N > 2000`, considerar ANN/LSH en vez de all-pairs

## Guards recomendados

```kotlin
val pixelCount = width * height
require(pixelCount <= MAX_PIXELS)

val estimatedMemory = batchSize * estimatedPerItemBytes
if (estimatedMemory > MEMORY_BUDGET) {
    batchSize = MEMORY_BUDGET / estimatedPerItemBytes
}
```

## Patrones de concurrencia

| Patron | Mejor cuando | Tradeoff |
|---|---|---|
| secuencial | poco volumen, stages simples | facil pero lento |
| `Flow.flatMapMerge` | IO-bound con backpressure | simple y expresivo |
| workers + channel | CPU-bound con control fino | mas complejo |
| `chunked` + `async` | batch orientado | backpressure manual |

## Heuristicas rapidas

- IO-bound: concurrencia baja-media, tipicamente 2-8
- CPU-bound: no exceder cores utiles
- memory-bound: limitar por RAM antes que por CPU
- hybrid: separar lecturas IO de decode/procesamiento CPU

## Que justificar en la spec

- por que elegiste ese patron
- cuantas unidades concurrentes soporta
- que stage domina el costo
- que haras si cambia el volumen de entrada
