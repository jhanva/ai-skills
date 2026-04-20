# Godot Setup — Export Presets Reference

Lee este archivo solo cuando vayas a definir o justificar export presets concretos.

## Presets iniciales recomendados

- Windows Desktop: baseline para pruebas locales y playtests
- HTML5: opcional si el juego apunta a itch.io, demos web o validacion rapida
- Linux/macOS: agregarlos cuando el target lo requiera, no por defecto

## Campos a decidir

- `export_path`
- `exclude_filter`
- embed de PCK
- texture compression por plataforma
- resize/canvas policy si es HTML5

## Reglas

- Empezar con 1-2 presets funcionales, no con todos
- Excluir `design/`, `tests/`, markdown y artefactos de repo
- Mantener nombres de binario y rutas consistentes con `builds/`
- Documentar limitaciones de la plataforma solo si afectan el proyecto

## Salida sugerida

- Tabla corta por preset
- Solo las keys de `export_presets.cfg` realmente necesarias
- Checklist final de export y smoke test
