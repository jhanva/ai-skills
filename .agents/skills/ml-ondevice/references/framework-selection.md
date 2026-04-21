# ML On-Device — Framework Selection

Lee este archivo solo cuando debas elegir framework o defender la decision.

## Tabla rapida

| Framework | Mejor para | Ventaja | Tradeoff |
|---|---|---|---|
| MediaPipe Tasks | embedding, clasificacion, deteccion, segmentacion con modelos compatibles | setup rapido | menos flexible |
| ML Kit | OCR, barcode, face, pose, selfie segmentation | integracion muy simple | casi sin customizacion |
| TFLite | modelos custom exportados desde TensorFlow o Keras | control total | mas trabajo de integracion |
| ONNX Runtime | modelos de PyTorch o HuggingFace | portabilidad | setup y optimizacion mas manuales |

## Decision tree

1. Si la tarea ya existe en ML Kit y la app prioriza simplicidad, empieza por ML Kit.
2. Si la tarea coincide con MediaPipe Tasks y el catalogo cubre el caso, MediaPipe suele ser la opcion mas rapida.
3. Si el modelo es custom y viene de TensorFlow, TFLite suele ser el baseline.
4. Si el modelo viene de PyTorch o ya existe en ONNX, ONNX Runtime evita conversiones agresivas.

## Que justificar

- por que ese framework cubre la tarea
- costo de integracion
- control sobre preprocessing
- estrategia de fallback
- impacto en binario y tiempo de inferencia
