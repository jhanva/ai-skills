# Image Pipeline — Progress, Errors, and Cache

Lee este archivo solo cuando definas observabilidad, cancelacion, politica de errores o persistencia.

## Progreso

Conviene reportar:

- fase actual
- `current / total`
- item actual opcional

No emitas progreso por cada item. Usa throttling por tiempo o por lote.

## Cancelacion

Checkpoints utiles:

1. antes de procesar cada item
2. entre stages
3. dentro de operaciones largas

En cancelacion, limpia:

- archivos temporales
- estado parcial en DB
- estado de UI

## Politica de errores

Patron base:

- permiso denegado o source roto: abort
- item corrupto o faltante: skip + log
- OOM o timeout recuperable: retry 1x y luego skip
- fallos persistentes en persistencia: abort

Define cuando el pipeline pasa de best-effort a fail-fast. Una regla comun es abortar si falla mas de la mitad de los items o si falla el stage fuente.

## Cache e incremental

Cachea resultados costosos como:

- hashes
- embeddings
- resultados intermedios estables

Invalidacion minima:

- tamano + `lastModified`
- version del algoritmo
- borrado explicito de archivos eliminados

Si el pipeline se re-ejecuta seguido, preferir delta incremental sobre reprocesar todo.
