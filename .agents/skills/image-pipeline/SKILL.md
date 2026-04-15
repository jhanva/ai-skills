---
name: image-pipeline
description: Diseña arquitecturas de pipelines de procesamiento de imágenes, etapas, buffers, errores y caching. Úsala cuando el usuario pida explícitamente estructurar un pipeline de imagen multi-paso. No la uses para fixes pequeños sin trabajo de arquitectura.
---

# Image Pipeline — Diseño de pipelines de procesamiento de imagen

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$image-pipeline`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Objetivo

Disenar un pipeline de procesamiento de imagen multi-paso con arquitectura correcta:
stages bien definidos, memory budget, concurrency, progress, cancellation, errores,
y caching. El output es una spec de arquitectura lista para `$plan`.

---

## FASE 1: Definir stages

### 1.1 Identificar cada paso

Mapear el pipeline completo con el usuario. Cada stage tiene:

```
[Nombre] → input type → operacion → output type → puede fallar? → cancelable?
```

Ejemplo (duplicate finder scan):
```
[Source]   MediaStore query    → List<ImageUri>       → si (permiso) → si
[Batch]   chunk(500)          → List<List<ImageUri>>  → no           → si
[Load]    ContentResolver     → ByteArray             → si (IO)      → si
[Hash]    MD5 + pHash         → HashResult            → no (CPU)     → si
[Store]   Room insert         → Unit                  → si (DB)      → si
[Compare] LSH + Hamming       → DuplicateGroups       → no (memory)  → no
[Display] StateFlow emission  → UiState               → no           → no
```

### 1.2 Clasificar stages

| Tipo | Bound por | Dispatcher | Ejemplos |
|---|---|---|---|
| IO-bound | Disco/red | Dispatchers.IO | MediaStore query, file read, network fetch |
| CPU-bound | Procesamiento | Dispatchers.Default | Hashing, ML inference, similarity calc |
| Memory-bound | RAM | Dispatchers.Default | Bitmap decode, similarity matrix, batch collect |
| UI-bound | Main thread | Dispatchers.Main | Progress update, state emission |

---

## FASE 2: Memory budget

### 2.1 Calcular peak por stage

Para cada stage, estimar memoria maxima:

| Stage | Formula | Ejemplo |
|---|---|---|
| Bitmap decode | width × height × 4 bytes (ARGB_8888) | 4000×3000 = 48MB |
| Bitmap scaled | targetW × targetH × 4 | 384×384 = 0.6MB |
| ML embedding | dimension × 4 bytes | 1024 × 4 = 4KB |
| Hash string | ~64 chars = 128 bytes | negligible |
| Similarity matrix | N × N × 4 bytes | 1000×1000 = 4MB |
| Collection of results | N × result_size | depende |

### 2.2 Calcular peak concurrente

```
peak_memory = concurrent_items × max_stage_memory

Ejemplo con 4 workers:
  4 bitmaps in-flight × 48MB = 192MB  → PELIGRO en devices de 4GB
  4 bitmaps scaled × 0.6MB = 2.4MB    → OK
```

### 2.3 Definir limites

| Constraint | Recomendacion |
|---|---|
| Peak per item | <50MB (bitmap no puede exceder esto) |
| Peak total | <200MB (considerar que la app usa memoria para UI, caches, etc.) |
| Collection size | Si N > 5000 items, paginar o usar cursor |
| Similarity matrix | Si N > 2000, usar LSH/ANN en vez de all-pairs |

### 2.4 Size guards

Definir guards explicitos:

```kotlin
// Bitmap size guard
val pixelCount = width * height
require(pixelCount <= MAX_PIXELS) { "Image too large: ${pixelCount} pixels" }

// Collection size guard
if (images.size > MAX_PAIRWISE) {
    // Switch to approximate algorithm or paginate
}

// Batch memory guard
val estimatedMemory = batchSize * estimatedPerItemBytes
if (estimatedMemory > MEMORY_BUDGET) {
    batchSize = MEMORY_BUDGET / estimatedPerItemBytes
}
```

---

## FASE 3: Concurrency model

### 3.1 Elegir patron

| Patron | Cuando usar | Backpressure | Complejidad |
|---|---|---|---|
| Sequential `forEach` | <50 items, stages rapidos | N/A | Baja |
| `Flow.flatMapMerge(concurrency)` | IO-bound, backpressure natural | Si | Media |
| `Channel` + worker coroutines | CPU-bound, control fino de workers | Si | Alta |
| `chunked` + `async` | Batch-oriented, items independientes | Manual | Media |

### 3.2 Patron recomendado por tipo

**IO-bound (file read, network):**
```kotlin
imageUris.asFlow()
    .flatMapMerge(concurrency = 4) { uri ->
        flow { emit(loadImage(uri)) }
    }
    .collect { result -> store(result) }
```

**CPU-bound (hash, ML):**
```kotlin
val channel = Channel<IndexedValue<Uri>>(capacity = Channel.BUFFERED)
val results = Array<Result?>(items.size) { null }

// Producer
launch { items.forEachIndexed { i, uri -> channel.send(IndexedValue(i, uri)) } }

// Workers (N = CPU cores / 2, min 2, max 8)
repeat(workerCount) {
    launch(Dispatchers.Default) {
        for ((index, uri) in channel) {
            results[index] = process(uri)
        }
    }
}
```

**Hybrid (IO + CPU stages):**
```kotlin
imageUris.asFlow()
    .flatMapMerge(4) { uri ->
        flow {
            val bytes = withContext(Dispatchers.IO) { readFile(uri) }
            val bitmap = withContext(Dispatchers.Default) { decode(bytes) }
            val result = withContext(Dispatchers.Default) { process(bitmap) }
            emit(result)
        }
    }
```

### 3.3 Worker count heuristic

```kotlin
val cpuCores = Runtime.getRuntime().availableProcessors()
val workerCount = when {
    stage.isIoBound -> minOf(cpuCores, 8)      // IO puede usar mas workers
    stage.isCpuBound -> minOf(cpuCores / 2, 4) // CPU no gana con mas workers que cores
    stage.isMemoryBound -> minOf(2, MEMORY_BUDGET / perItemMemory) // limitado por RAM
}
```

---

## FASE 4: Progress y cancellation

### 4.1 Diseño de Progress

```kotlin
data class PipelineProgress(
    val phase: PipelinePhase,     // enum: SCANNING, LOADING, PROCESSING, STORING, COMPARING
    val current: Int,             // items procesados en esta fase
    val total: Int,               // total de items en esta fase
    val currentItem: String? = null  // nombre del item actual (opcional, para UI)
)
```

La funcion del pipeline retorna `Flow<PipelineProgress>`:

```kotlin
fun executePipeline(input: PipelineInput): Flow<PipelineProgress>
```

### 4.2 Frecuencia de progress updates

No emitir en cada item — throttle para evitar saturar UI:

```kotlin
// Emitir cada N items O cada 100ms, lo que pase primero
if (current % progressStep == 0 || now - lastEmit > 100) {
    emit(PipelineProgress(phase, current, total))
    lastEmit = now
}

// progressStep heuristic
val progressStep = maxOf(1, total / 100)  // ~100 updates por fase
```

### 4.3 Cancellation checkpoints

Verificar `isActive` en estos puntos:

1. **Antes de procesar cada item** — punto de cancelacion natural
2. **Antes de cada stage transition** — cancelar entre fases
3. **Dentro de operaciones largas** — si un item tarda >1s, verificar mid-item

```kotlin
for ((index, item) in items.withIndex()) {
    ensureActive()  // checkpoint
    val result = process(item)
    results[index] = result
}
```

### 4.4 Cleanup on cancel

Definir que limpiar si el pipeline se cancela:

| Recurso | Cleanup |
|---|---|
| Bitmaps in-flight | Se liberan por GC (no necesita manual cleanup) |
| Archivos temporales | Borrar en `finally` block |
| DB state parcial | `@Transaction` wrapping, o flag de "incomplete" |
| UI state | Reset a idle en `finally` |

---

## FASE 5: Error strategy por stage

### 5.1 Definir politica por tipo de error

| Tipo de error | Politica recomendada |
|---|---|
| Permiso denegado | Abort pipeline, reportar al usuario |
| Archivo no encontrado | Skip item, log warning, continuar |
| Imagen corrupta/ilegible | Skip item, log warning, continuar |
| Decode OOM | Reducir inSampleSize, retry 1x, luego skip |
| ML inference timeout | Retry 1x, luego skip |
| DB write failure | Retry con backoff (3x), luego abort |
| Calculo in-memory | No deberia fallar — si falla, es bug, throw |

### 5.2 Error tracking

```kotlin
data class PipelineResult(
    val successful: Int,
    val skipped: Int,
    val errors: List<PipelineError>,  // archivo + razon
    val output: T                     // resultado del pipeline
)

data class PipelineError(
    val item: String,       // URI o nombre
    val stage: PipelinePhase,
    val reason: String
)
```

Reportar al final: "Procesadas 950/1000 imagenes. 50 saltadas (42 corruptas, 8 sin permiso)."

### 5.3 Fail-fast vs best-effort

| Escenario | Politica |
|---|---|
| >50% de items fallan | Abort — algo esta fundamentalmente mal |
| Source stage falla | Abort — no hay datos para procesar |
| Items individuales fallan | Best-effort — skip y continuar |
| Store stage falla repetidamente | Abort — no se puede persistir |

---

## FASE 6: Caching y persistencia

### 6.1 Que cachear

| Dato | Donde cachear | Invalidacion |
|---|---|---|
| Resultado de procesamiento (hash, embedding) | Room | Content hash (size + lastModified) |
| Bitmap decodificado para display | Coil/Glide memory+disk cache | LRU, TTL del server |
| Resultado intermedio costoso | Room o DataStore | Version del algoritmo |
| Resultado del pipeline completo | Room | Re-scan manual o file watcher |

### 6.2 Cache invalidation strategy

```kotlin
// Content hash = proxy barato para "archivo cambio?"
fun contentHash(size: Long, lastModified: Long): String = "${size}_${lastModified}"

// Check en pipeline
val cached = dao.getCachedResult(imageId)
if (cached != null && cached.contentHash == currentContentHash) {
    return cached.result  // cache hit, skip processing
}
// cache miss o stale, re-process
```

### 6.3 Incremental processing

Si el pipeline se ejecuta multiples veces (re-scan):

1. Detectar archivos nuevos/modificados/eliminados vs ultima ejecucion
2. Solo procesar nuevos + modificados
3. Limpiar datos de eliminados
4. Esto convierte un O(N) completo en O(delta) incremental

---

## FASE 7: Spec de salida

Producir documento con:

1. **Pipeline diagram:** stages con tipos de input/output
2. **Memory budget:** peak por stage, peak concurrente, size guards
3. **Concurrency model:** patron elegido con justificacion, worker count
4. **Progress/cancellation:** formato de Progress, checkpoints, cleanup
5. **Error strategy:** politica por stage, fail-fast vs best-effort threshold
6. **Caching:** que se cachea, donde, como se invalida
7. **Clean Architecture mapping:**
   - Que vive en domain (use case, repository interface, Progress model)
   - Que vive en data (repository impl, DAO, cache logic)
   - Que vive en presentation (ViewModel, progress UI)
8. **Performance targets:** tiempo total para N items, memoria max

Transicion: "Usa `$plan` para convertir este diseño en tareas de implementacion."

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
