---
name: bitmap-safety
description: Audita pipelines de imágenes en Android para detectar riesgos de OOM, threading incorrecto, EXIF ignorado y manejo inseguro de bitmaps. Úsala cuando el usuario pida explícitamente revisar procesamiento de imágenes Android. No la uses para tareas generales de UI ni para proyectos sin bitmaps.
---

# Bitmap Safety — Auditoria de pipelines de imagen

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$bitmap-safety`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Ley de hierro: READ-ONLY

**PROHIBIDO modificar archivos.** Solo reportar hallazgos inline.

## Resolver target

1. Si el prompt incluye una ruta, usarla como target
2. Si el prompt no especifica ruta, usar el directorio actual
3. Validar que contiene codigo Android (buscar `build.gradle*`)

---

## FASE 1: Reconocimiento de imagen

Identificar como el proyecto maneja imagenes:

```
# Image loading libraries
Busca con `rg -n`: "io.coil-kt" | "com.bumptech.glide" | "com.squareup.picasso"

# Direct bitmap operations
Busca con `rg -n`: "BitmapFactory" | "Bitmap.createBitmap" | "Bitmap.createScaledBitmap"

# ML/Vision
Busca con `rg -n`: "MediaPipe" | "MLKit" | "TensorFlow" | "ONNX"

# Image hashing
Busca con `rg -n`: "MessageDigest" | "perceptualHash" | "phash" | "dhash"

# EXIF
Busca con `rg -n`: "ExifInterface"

# Content loading
Busca con `rg -n`: "ContentResolver" | "openInputStream" | "MediaStore"
```

Clasificar el proyecto:
- **Image viewer** (Coil/Glide only, no processing)
- **Image processor** (decode, transform, hash, embed)
- **Hybrid** (viewer + processing)

---

## FASE 2: Bitmap Decode Safety

### Check 1 — inSampleSize

Buscar todo uso de `BitmapFactory.decode*`:

```
BitmapFactory.decodeStream
BitmapFactory.decodeFile
BitmapFactory.decodeResource
BitmapFactory.decodeByteArray
```

Para cada uno verificar:
- Usa `BitmapFactory.Options` con `inSampleSize` calculado? (no hardcoded)
- Hace two-pass decode? (primer pass con `inJustDecodeBounds = true`)
- Si `inSampleSize` es hardcoded (ej: `inSampleSize = 4`), reportar como IMPORTANTE — debe calcularse relativo al tamaño target

**Excepcion:** Si el bitmap se decodifica a un tamaño fijo conocido muy pequeno (<100px), hardcoded es aceptable.

### Check 2 — Size guards

Buscar `Bitmap.createBitmap(width, height, ...)`:
- Hay validacion de que width*height no exceda un limite?
- Se usa en loops o con tamaños derivados de input externo?
- Sin guard, una imagen de 10000x10000 = 400MB de RAM

Buscar colecciones de bitmaps (`List<Bitmap>`, `Array<Bitmap>`, `MutableList<Bitmap>`):
- Crecen sin limite?
- Se reciclan/liberan?

### Check 3 — EXIF orientation

Si el proyecto decodifica bitmaps directamente (no via Coil/Glide que manejan EXIF automaticamente):
- Se usa `ExifInterface` para leer orientacion?
- Se aplica `Matrix.postRotate()` segun el tag?
- Si no, las fotos tomadas en portrait apareceran rotadas

---

## FASE 3: Memory & Threading

### Check 4 — Threading

Buscar operaciones pesadas de bitmap:

```
BitmapFactory.decode*
Bitmap.createBitmap
Bitmap.createScaledBitmap
MessageDigest (hashing)
ImageEmbedder (ML inference)
```

Verificar que NO estan en:
- `Dispatchers.Main` / `Main.immediate`
- `lifecycleScope.launch { }` sin dispatcher explicito (default = Main)
- `viewModelScope.launch { }` sin dispatcher explicito (default = Main)

Deben estar en `Dispatchers.Default` (CPU-bound) o `Dispatchers.IO` (file read).

### Check 5 — Algoritmos O(n^2) o peor

Buscar loops anidados sobre colecciones de imagenes:

```kotlin
// Patron peligroso: comparacion all-vs-all
for (i in images.indices) {
    for (j in i + 1 until images.size) {
        similarity(images[i], images[j])
    }
}
```

Si existe, verificar:
- Hay size guard? (ej: if images.size > MAX throw/paginate)
- Se usa una estructura de aceleracion? (LSH, KD-tree, bucketing)
- Sin guard, 1000 imagenes = 500K comparaciones, 10000 = 50M

### Check 6 — Batch processing

Si se procesan imagenes en batch (indexing, scanning):
- Hay control de concurrencia? (semaphore, channel con capacidad limitada)
- Hay progreso reportado? (Flow<Progress>, setProgress())
- Hay cancelacion? (isActive check, CancellationException handling)
- Se liberan bitmaps despues de procesarlos? (o se acumulan en memoria)

---

## FASE 4: Image Loading Library Config

### Coil

Buscar `ImageLoader.Builder` o `ImageLoader(context)`:

- `memoryCache`: esta configurado? tamaño razonable? (default 25% app memory)
- `diskCache`: esta configurado? tamaño limite?
- `crossfade`: habilitado para UX?
- `error()` / `placeholder()`: definidos? (sin ellos, fallos de carga son invisibles)
- `respectCacheHeaders`: esta en true? (si es false, cache nunca expira)

### Glide

Buscar `GlideModule` o `@GlideModule`:
- `setMemorySizeCalculator`: esta customizado?
- `setDiskCacheFactory`: tamaño definido?
- Error/placeholder drawables definidos?

### Sin library (decode directo)

Si el proyecto NO usa Coil/Glide para display sino decode directo:
- Reportar como IMPORTANTE — considerar usar una library que maneje cache, memory, threading, y EXIF automaticamente
- Si hay razones legitimas (ML preprocessing, hashing), verificar que los checks 1-6 se cumplen manualmente

---

## FASE 5: Error Handling en Imagen

### Check 7 — Fallos silenciosos

Buscar patrones de error handling en operaciones de imagen:

```kotlin
// PELIGROSO — fallo silencioso
try { loadBitmap(uri) } catch (e: Exception) { null }

// PELIGROSO — return null sin log
fun loadImage(uri: Uri): Bitmap? {
    return try { ... } catch (e: Exception) { null }
}
```

Verificar:
- Se loggea el error? (al menos Log.w)
- Se reporta al usuario? (placeholder de error, toast, retry)
- Imagenes corruptas/faltantes se saltan silenciosamente o se reportan?

---

## FASE 6: Reporte

```markdown
## Auditoria de bitmap safety

### CRITICO (riesgo de OOM/ANR en produccion)
- `ml/BitmapLoader.kt:45` — BitmapFactory.decodeStream sin inSampleSize
  Impacto: imagen de 4000x3000 = 48MB en RAM, OOM en dispositivos con poca memoria
  Fix: agregar two-pass decode con inSampleSize calculado

### IMPORTANTE (bug latente)
- `ml/ManualVisualClusterer.kt:89` — O(n^2) buildSimilarityMatrix sin size guard
  Impacto: 1000 imagenes = 500K comparaciones, posible ANR
  Fix: agregar guard `if (images.size > MAX_PAIRWISE) throw/paginate`

### MENOR (mejora recomendada)
- `presentation/ResultsScreen.kt:120` — AsyncImage sin error() drawable
  Impacto: fallos de carga son invisibles para el usuario
  Fix: agregar `.error(R.drawable.error_placeholder)`

### Resumen
| Severidad | Cantidad |
|---|---|
| Critico | N |
| Importante | N |
| Menor | N |

Tipo de proyecto: [Image processor/viewer/hybrid]
Libraries detectadas: [Coil 2.5.0, MediaPipe 0.10.9, etc.]
Archivos de imagen escaneados: N
```

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
