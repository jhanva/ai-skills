# ML On-Device — Runtime Playbook

Lee este archivo solo cuando diseñes preprocessing, runtime o testing.

## Preprocessing base

Checklist minima:

1. decode con sampling, no bitmap full-size
2. correccion EXIF
3. resize al input del modelo
4. color space correcto
5. normalizacion correcta

## Wrapper recomendado

El wrapper debe tener:

- `initialize()`
- `close()`
- `isReady()`
- `process(bitmap)` o equivalente
- configuracion de delegate si aplica

## Runtime

Defaults utiles:

- fallback GPU -> CPU cuando el delegate falle
- `Mutex` como baseline de thread safety si solo hay una instancia del modelo
- lazy init como default
- timeout por inferencia y por inicializacion

## Domain mapping

Convierte siempre el output raw a tipos del dominio:

- embedding -> vector del dominio
- clasificacion -> label + confidence
- deteccion -> rect + label + score
- segmentacion -> resultado con mascara y metadata

## Testing

Minimo recomendado:

- golden images
- test de preprocessing
- test de postprocessing
- test de integracion del wrapper
- benchmark sencillo de inferencia

Si GPU y CPU difieren levemente, documenta una tolerancia de precision en vez de exigir igualdad exacta.
