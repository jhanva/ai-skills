# Game Arch — Save and Rendering

Lee este archivo solo cuando definas persistencia o rendering.

## Save system

Reglas base:

- guardar IDs, no referencias vivas
- versionar el formato
- no guardar estado derivado si puede recalcularse
- usar escritura atomica cuando sea posible

Anti-patrones:

- guardar en momentos inestables
- no tener camino de migracion
- serializar tipos del runtime grafico o de escena

## Rendering

Checklist minima:

- orden de render claro
- no crear texturas o batches por frame
- atlas y filtering consistentes
- camera follow y resize definidos

Idealmente:

- un batch por frame salvo que haya una razon fuerte
- assets con lifecycle claro
- `dispose()` o manejo via asset manager
