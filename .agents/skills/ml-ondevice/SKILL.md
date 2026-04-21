---
name: ml-ondevice
description: Diseña integración de modelos ML on-device en Android, inferencia, pre/post-procesado y tradeoffs de runtime. Úsala cuando el usuario pida explícitamente ayuda con ML local en Android. No la uses para ML server-side o para apps no Android.
---

# ML On-Device — Integracion de modelos ML en Android

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$ml-ondevice`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, asume defaults razonables y declaralos; pregunta solo por requisitos que cambian framework, latencia o output esperado.
- Delega solo si el usuario pidio paralelismo o delegacion.

## Objetivo

Disenar la integracion completa de un modelo ML on-device: framework, preprocessing, inference wrapper, mapping al domain layer, runtime seguro y testing.

## Carga just-in-time

- Lee `references/framework-selection.md` cuando debas elegir entre MediaPipe, ML Kit, TFLite u ONNX Runtime.
- Lee `references/runtime-playbook.md` cuando definas preprocessing, delegates, thread safety, lifecycle o testing.

## FASE 1: Definir la tarea ML

Aclara o infiere:

- tipo de tarea: embedding, clasificacion, deteccion, segmentacion, OCR u otra
- tipo de input: camara, galeria, screenshot, stream, batch
- output que necesita el domain layer
- latencia aceptable
- volumen esperado
- si el proyecto ya tiene infraestructura ML

Busca primero implementaciones existentes con `rg -n` para `MediaPipe|MLKit|TFLite|onnxruntime|ImageEmbedder|ImageClassifier|ObjectDetector`.

## FASE 2: Elegir framework

Haz la seleccion por:

- tipo de tarea
- si el modelo es catalogo Google o custom
- facilidad de setup
- portabilidad
- control sobre preprocessing y runtime

Si la decision no es trivial, lee `references/framework-selection.md`.

## FASE 3: Disenar el contrato de integracion

Define:

- preprocessing desde el input real hasta el tensor o wrapper esperado
- wrapper de inferencia con lifecycle claro
- postprocessing hacia tipos del domain layer
- dependencias exactas a introducir

Regla: el domain layer no debe conocer tipos propios del framework ML.

## FASE 4: Runtime seguro

Define:

- estrategia de delegate y fallback
- thread safety
- lifecycle del modelo
- timeouts
- ubicacion por capas y DI

Para este bloque, lee `references/runtime-playbook.md`.

## FASE 5: Testing

Incluye:

- golden images o fixtures
- tests de preprocessing
- tests de postprocessing
- tests de integracion del wrapper
- benchmark o target de performance cuando aplique

## FASE 6: Spec de salida

El documento final debe cubrir:

1. tarea ML e input/output
2. framework elegido con justificacion
3. preprocessing completo
4. postprocessing y mapping al domain layer
5. runtime seguro
6. ubicacion por capas y DI
7. estrategia de testing
8. dependencias exactas

Transicion: recomendar `$image-pipeline` si esto forma parte de un pipeline mayor, o `$plan` si ya esta listo para implementar.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
