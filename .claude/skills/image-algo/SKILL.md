---
name: image-algo
description: >
  Diseño de algoritmos de procesamiento de imagen con validacion formal.
  Cubre hashing, similarity, clustering, quality scoring, y deteccion.
  Incluye edge cases especificos de imagen, metricas de accuracy,
  y analisis de complejidad on-device.
when_to_use: >
  Cuando el usuario quiere disenar un algoritmo de imagen nuevo: similarity,
  hashing, clustering, quality scoring, deteccion, clasificacion.
  Tambien cuando dice "image-algo", "algoritmo de imagen", "como comparo imagenes",
  "como detecto duplicados", "como mido calidad".
argument-hint: "[descripcion del problema]"
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

# Image Algo — Diseño de algoritmos de imagen

## Objetivo

Disenar un algoritmo de procesamiento de imagen con fundamento matematico,
edge cases identificados, metricas de validacion, y analisis de feasibility on-device.
El output es una spec tecnica lista para `/plan` o `/tdd`.

---

## FASE 1: Formalizar el problema

### 1.1 Definir input/output

Clarificar con el usuario:

| Pregunta | Opciones tipicas |
|---|---|
| Input | Bitmap raw, embedding vector, metadata (EXIF, size), file bytes |
| Output | Score 0-1, booleano, ranking, clusters, labels, bounding boxes |
| Granularidad | Per-image, per-pair, per-batch |
| Ground truth | Que define "correcto"? (human labels, known duplicates, reference set) |

### 1.2 Clasificar el tipo de problema

| Tipo | Ejemplo | Metricas clave |
|---|---|---|
| Similarity/matching | "Estas 2 imagenes son parecidas?" | Precision, recall, F1, ROC-AUC |
| Clustering | "Agrupa imagenes similares" | Silhouette score, homogeneity, completeness |
| Scoring | "Que tan nitida es esta imagen?" | Correlacion con ranking humano (Spearman/Kendall) |
| Detection | "Tiene texto? Tiene caras?" | Precision, recall, IoU (si hay bboxes) |
| Classification | "Es foto, screenshot, o render?" | Accuracy, confusion matrix |

---

## FASE 2: Explorar approaches

Proponer 2-3 approaches con tradeoffs claros. Para cada uno:

### Niveles de abstraccion

**Pixel-level (sin ML):**
- Ventaja: determinista, rapido, sin modelo que cargar
- Limitacion: fragil ante transformaciones (crop, resize, recompresion)
- Ejemplos:
  - DCT → perceptual hash (pHash): robusto a resize/recompresion leve
  - Laplacian variance: mide sharpness/blur
  - Color histogram comparison: similarity por distribucion de color
  - Difference hash (dHash): detecta cambios estructurales
  - SSIM: similarity perceptual pixel a pixel

**Feature-level (ML embeddings):**
- Ventaja: robusto a transformaciones, captura semantica
- Limitacion: requiere modelo (~5-50MB), inference time, GPU opcional
- Ejemplos:
  - MobileNet embeddings: proposito general, buena relacion costo/accuracy
  - CLIP embeddings: multimodal (texto + imagen), mas pesado
  - ResNet/EfficientNet: alta accuracy, mas lento
  - Face embeddings (ArcFace): especifico para rostros

**Statistical:**
- Ventaja: rapido, interpretable
- Limitacion: pierde informacion espacial
- Ejemplos:
  - Histogramas de color (RGB, HSV)
  - Momentos de imagen (Hu moments)
  - Distribucion de frecuencias (FFT)

**Hybrid:**
- Combinar approaches para balancear velocidad y accuracy
- Ejemplo: pre-filtro rapido (pHash) + validacion fina (ML embedding)
- Ejemplo: centroid similarity + topK scoring (como ImageSorter)

### Tabla comparativa por approach

Para cada approach propuesto, llenar:

| Criterio | Approach A | Approach B | Approach C |
|---|---|---|---|
| Accuracy esperada | | | |
| Complejidad (time) | | | |
| Complejidad (space) | | | |
| Tamaño de modelo | N/A o NMB | | |
| Robusto a crop/resize | | | |
| Robusto a recompresion | | | |
| Robusto a cambio de luz | | | |
| Implementacion (esfuerzo) | | | |

---

## FASE 3: Edge cases de imagen

Revisar TODOS estos edge cases contra el approach elegido. Para cada uno,
documentar el comportamiento esperado:

### Transformaciones geometricas
- Rotacion 90/180/270 (EXIF orientation)
- Flip horizontal/vertical
- Crop parcial (10%, 30%, 50% del area)
- Resize extremo (thumbnail 50px vs original 4000px)
- Aspect ratio diferente (misma imagen cortada)

### Condiciones de captura
- Muy oscura / muy brillante / HDR
- Motion blur vs static blur vs out-of-focus
- Ruido (ISO alto, poca luz)
- Contralight / backlit

### Formato y compresion
- JPEG quality 10 vs 50 vs 95
- PNG vs JPEG vs WebP (misma imagen, diferentes artifacts)
- Screenshots (bordes filosos, texto, solid colors)
- Imagenes con alpha channel / transparencia

### Contenido
- Imagenes con mucho texto vs escenas naturales
- Imagenes casi identicas pero con marca de agua
- Imagenes solidas (un solo color)
- Imagenes muy pequenas (<100px)
- Imagenes muy grandes (>50MP, >100MB)
- Animated GIF / multi-frame

### Adversarial
- Imagen identica pero con 1 pixel cambiado
- Mirror image (flip horizontal)
- Mismo contenido con borde/marco agregado
- Meme: misma imagen con texto overlay diferente

Para cada edge case relevante, definir:
- Comportamiento esperado (match, no-match, score esperado)
- Si el approach elegido lo maneja correctamente
- Si necesita handling especial (pre-procesamiento)

---

## FASE 4: Metricas y validacion

### 4.1 Definir test strategy

```
Test set minimo para algoritmos de imagen:
- 10 pares known-duplicate (exactos)
- 10 pares known-similar (near-duplicate)
- 10 pares known-different (no relacionados)
- 5 edge cases de la Fase 3 que sean criticos para el use case
```

### 4.2 Metricas por tipo de problema

**Similarity/matching:**
- True positive rate @ threshold T
- False positive rate @ threshold T
- ROC curve: variar threshold, graficar TPR vs FPR
- Threshold optimo: punto de la curva que maximice F1

**Clustering:**
- Silhouette score (>0.5 = bueno, >0.7 = excelente)
- Numero de clusters vs expected (si se conoce)
- Purity: % de items en cluster correcto

**Scoring:**
- Correlacion con ground truth (ranking humano o known quality)
- Distribucion de scores: debe separar bien bueno/malo

### 4.3 Performance benchmarks

Medir en device target (o emulador con specs similares):

| Metrica | Target razonable |
|---|---|
| Tiempo por imagen (sin ML) | <50ms |
| Tiempo por imagen (con ML) | <200ms |
| Memoria peak por imagen | <50MB |
| Memoria total para N=1000 | <200MB |
| Batch de 100 imagenes | <30s |

---

## FASE 5: Spec de salida

Producir documento con:

1. **Problema:** definicion formal (input, output, ground truth)
2. **Approach elegido:** con justificacion vs alternativas
3. **Algoritmo paso a paso:** pseudocodigo con tipos
4. **Edge cases:** tabla con comportamiento esperado por caso
5. **Metricas:** que medir, que valores son aceptables
6. **Complejidad:** time O(?), space O(?), feasibility on-device
7. **Test plan:** test set, golden images, automation

Esta spec es el input para `/plan` o directamente para `/tdd`.

---

## Transicion

Cuando el usuario aprueba la spec:
- Si requiere ML: "Usa `/ml-ondevice` para disenar la integracion del modelo"
- Si requiere pipeline multi-paso: "Usa `/image-pipeline` para disenar la arquitectura del pipeline"
- Si esta listo para implementar: "Usa `/plan` para convertir esto en tareas"

## Argumento: $ARGUMENTS
