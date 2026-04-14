---
name: ml-ondevice
description: >
  Guia la integracion de modelos ML on-device en Android. Cubre seleccion
  de framework (MediaPipe/MLKit/TFLite/ONNX), preprocessing, postprocessing,
  GPU/CPU fallback, lifecycle del modelo, thread safety, y testing.
when_to_use: >
  Cuando el usuario quiere integrar un modelo ML en una app Android.
  Tambien cuando dice "ml-ondevice", "agregar modelo", "MediaPipe", "TFLite",
  "ML Kit", "ONNX", "inferencia", "embedding", "deteccion", "clasificacion on-device".
argument-hint: "[descripcion del modelo o tarea ML]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Bash(find *)
  - Bash(wc *)
  - WebFetch
  - WebSearch
---

# ML On-Device — Integracion de modelos ML en Android

## Objetivo

Disenar la integracion completa de un modelo ML on-device: seleccion de framework,
preprocessing, inference, postprocessing, fallback, lifecycle, threading, y testing.
El output es una spec de integracion lista para `/plan`.

---

## FASE 1: Definir la tarea ML

### 1.1 Clarificar con el usuario

| Pregunta | Por que importa |
|---|---|
| Que tarea? (embedding, clasificacion, deteccion, segmentacion) | Define el tipo de modelo |
| Que input? (foto de camara, imagen de galeria, screenshot, stream) | Define preprocessing |
| Que output necesita el domain layer? | Define postprocessing |
| Latencia aceptable? (<100ms, <500ms, <2s) | Define modelo size/complexity |
| Debe funcionar offline? | Todos los on-device funcionan offline, pero MLKit puede necesitar download inicial |
| Volumen? (1 imagen, batch de 100, stream continuo) | Define threading y memory strategy |

### 1.2 Verificar si ya existe algo en el proyecto

```
# Buscar ML existente
Grep: "MediaPipe|MLKit|TFLite|tensorflow|onnxruntime|ImageEmbedder|ImageClassifier|ObjectDetector"

# Buscar wrappers existentes
Grep: "Embedder|Classifier|Detector|Segmenter" en archivos .kt
```

Si ya hay infraestructura ML, reutilizar patterns existentes (wrappers, DI, fallback).

---

## FASE 2: Seleccion de framework

### Tabla de decision

| Framework | Mejor para | Modelo size | Setup | Customizacion |
|---|---|---|---|---|
| **MediaPipe Tasks** | Embedding, clasificacion, deteccion, segmentacion con modelos Google | 5-30MB | Facil (1 dependency) | Limitado a catalogo Google, modelos custom via TFLite |
| **ML Kit** | OCR, barcode, face detection, pose, selfie segmentation | 1-15MB (on-device) o 0 (cloud) | Muy facil (Play Services) | Nula — solo modelos de Google |
| **TFLite** | Modelos custom (fine-tuned, exportados de TF/Keras) | Variable | Medio | Total — cualquier modelo .tflite |
| **ONNX Runtime** | Modelos de PyTorch/HuggingFace, cross-platform | Variable | Medio | Total — cualquier modelo .onnx |

### Decision tree

```
Necesitas modelo custom?
├─ NO → Tarea esta en catalogo de MediaPipe Tasks?
│       ├─ SI → MediaPipe Tasks
│       └─ NO → Tarea esta en ML Kit?
│               ├─ SI → ML Kit
│               └─ NO → TFLite con modelo pre-trained
└─ SI → Modelo viene de PyTorch?
        ├─ SI → ONNX Runtime (o convertir a TFLite)
        └─ NO → TFLite
```

---

## FASE 3: Disenar preprocessing

### 3.1 Input pipeline

Para cada framework, el modelo espera un formato especifico:

**MediaPipe:**
```kotlin
// Input: MPImage (wrapper de Bitmap/ByteBuffer)
val mpImage = BitmapImageBuilder(bitmap).build()
```

**TFLite:**
```kotlin
// Input: ByteBuffer con shape [1, height, width, channels]
// Requiere: resize a tamaño fijo, normalizar pixels (0-1 o -1..1)
val inputBuffer = ByteBuffer.allocateDirect(1 * 224 * 224 * 3 * 4)
```

**ONNX:**
```kotlin
// Input: OnnxTensor con shape especifica del modelo
val tensor = OnnxTensor.createTensor(env, floatArray, shape)
```

### 3.2 Bitmap preparation

Disenar la funcion de preparacion del bitmap:

1. **Decode con sampling** — nunca cargar bitmap full-size para ML
   - Calcular `inSampleSize` relativo al input size del modelo
   - Two-pass decode (bounds → sample → decode)

2. **EXIF correction** — aplicar rotacion antes de inference
   - Modelos no son orientation-aware por default

3. **Resize al input size del modelo** — `Bitmap.createScaledBitmap` o `Matrix`
   - Preservar aspect ratio? (letterbox con padding negro vs stretch)
   - Center crop vs fit?

4. **Color space** — verificar que el modelo espera RGB vs BGR
   - MediaPipe maneja esto internamente
   - TFLite/ONNX: conversion manual puede ser necesaria

5. **Normalization** — escalar pixels al rango del modelo
   - [0, 1]: dividir por 255
   - [-1, 1]: (pixel / 127.5) - 1
   - ImageNet normalization: (pixel - mean) / std por canal

Documentar la funcion completa con tipos:

```kotlin
fun prepareBitmap(uri: Uri): Bitmap {
    // 1. Two-pass decode con inSampleSize
    // 2. EXIF rotation
    // 3. Resize a MODEL_INPUT_SIZE
    // 4. Color space conversion (si necesario)
    // return bitmap listo para inference
}
```

---

## FASE 4: Inference y postprocessing

### 4.1 Inference wrapper

Disenar la clase wrapper con estas responsabilidades:

```kotlin
class ModelWrapper @Inject constructor(context: Context) {
    // Lifecycle
    fun initialize()         // Cargar modelo en memoria
    fun close()              // Liberar recursos
    fun isReady(): Boolean

    // Inference
    suspend fun process(bitmap: Bitmap): DomainResult  // Thread-safe

    // Config
    fun setDelegate(delegate: Delegate)  // GPU, NNAPI, CPU
}
```

### 4.2 Postprocessing

Convertir output raw del modelo a tipos del domain layer:

| Tarea ML | Output raw | Domain model |
|---|---|---|
| Embedding | FloatArray(N) | `EmbeddingVector(values: FloatArray)` |
| Clasificacion | FloatArray(classes) | `Classification(label: String, confidence: Float)` |
| Deteccion | List<BBox+score+label> | `Detection(rect: Rect, label: String, score: Float)` |
| Segmentacion | Mask bitmap | `SegmentationResult(mask: Bitmap, labels: Map<Int, String>)` |

Importante: el domain model NO debe contener tipos del framework ML.

### 4.3 Output normalization

- Embeddings: L2-normalizar si el modelo no lo hace (para dot product similarity)
- Scores: verificar rango (algunos modelos dan logits, no probabilidades)
- Bounding boxes: normalizar a coordenadas relativas (0-1) o absolutas (pixels)

---

## FASE 5: Runtime strategy

### 5.1 Delegate (GPU/CPU) fallback

```kotlin
// Estrategia recomendada
try {
    initializeWithGpu()
} catch (e: Exception) {
    Log.w(TAG, "GPU delegate failed, falling back to CPU", e)
    initializeWithCpu()
}

// Tambien manejar fallo en runtime (no solo en init)
suspend fun process(bitmap: Bitmap): Result {
    return try {
        inferenceWithCurrentDelegate(bitmap)
    } catch (e: Exception) {
        if (currentDelegate == GPU) {
            reinitializeWithCpu()
            inferenceWithCurrentDelegate(bitmap)  // retry con CPU
        } else throw e
    }
}
```

### 5.2 Thread safety

| Patron | Cuando usar |
|---|---|
| `Mutex` | Un solo modelo, multiples callers. Simple, funciona siempre |
| Thread confinement | Modelo solo accesible desde un dispatcher dedicado |
| Pool de instancias | Alto throughput, multiples modelos cargados. Complejo |

Para la mayoria de apps Android: **Mutex es suficiente.**

### 5.3 Model lifecycle

| Estrategia | Cuando usar |
|---|---|
| Lazy init (first use) | Modelo se usa ocasionalmente, no en startup |
| Eager init (app start) | Modelo se usa siempre, latencia de first use es inaceptable |
| Scoped (screen lifecycle) | Modelo solo se usa en una pantalla, liberar al salir |

Recomendar lazy init como default. Eager solo si el cold start es >2s y afecta UX.

### 5.4 Timeouts

| Operacion | Timeout recomendado |
|---|---|
| Model initialization | 30s (include download si aplica) |
| Single inference | 10-30s (depende del modelo) |
| Batch inference | Per-item timeout, no global |

---

## FASE 6: Testing strategy

### 6.1 Golden test images

Crear set de imagenes con output conocido:

```
test/resources/ml/
  golden_input_001.jpg     → expected_output_001.json
  golden_input_002.jpg     → expected_output_002.json
  edge_case_dark.jpg       → expected_output_dark.json
  edge_case_rotated.jpg    → expected_output_rotated.json
```

### 6.2 Tests por capa

| Capa | Que testear | Como |
|---|---|---|
| Preprocessing | Resize, EXIF, normalization | Unit test con bitmap de tamaño conocido |
| Postprocessing | Raw output → domain model | Unit test con output fijo |
| Wrapper integration | End-to-end con golden images | Instrumented test (necesita modelo real) |
| Domain use case | Logica de negocio sobre resultados ML | Unit test con mock del wrapper |

### 6.3 Determinism check

- Misma imagen → mismo output? (GPU vs CPU puede dar diferencias de precision)
- Definir tolerance: embeddings con cosine similarity > 0.999 = "mismo output"
- Documentar si el modelo es non-deterministic y como manejarlo en tests

### 6.4 Performance benchmark

```kotlin
@Test fun inferencePerformance() {
    val bitmap = loadGoldenImage()
    val times = (1..10).map { measureTimeMillis { wrapper.process(bitmap) } }
    val avg = times.average()
    val p95 = times.sorted()[8]
    assertTrue("Avg inference should be <${MAX_AVG_MS}ms", avg < MAX_AVG_MS)
}
```

---

## FASE 7: Spec de salida

Producir documento con:

1. **Tarea ML:** que hace el modelo, input/output
2. **Framework elegido:** con justificacion vs alternativas
3. **Preprocessing:** pipeline completo (decode → EXIF → resize → normalize)
4. **Postprocessing:** raw output → domain model mapping
5. **Runtime:** delegate fallback chain, thread safety, lifecycle, timeouts
6. **Clean Architecture placement:**
   - Interface en domain (`ImageAnalyzer`, `EmbeddingProvider`)
   - Implementacion en capa ml/ o data/
   - DI binding
7. **Testing:** golden images, tests por capa, performance benchmark
8. **Dependencies:** libraries exactas con versiones para build.gradle

Transicion: "Usa `/image-pipeline` si el modelo es parte de un pipeline multi-paso, o `/plan` para implementar directamente."

## Argumento: $ARGUMENTS
