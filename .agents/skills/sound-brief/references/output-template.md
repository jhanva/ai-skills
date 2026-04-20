# Sound Brief Output Template

Lee este archivo solo cuando vayas a escribir `design/audio/{system}-brief.md` o cuando necesites la plantilla completa.

## Documento sugerido

```markdown
# {System} Audio Brief

## SFX List
[Tabla trigger / description / duration / priority / variations / file]

## Music Tracks
[Tabla mood / tempo / instruments / duration / loop / adaptive]

## Audio Bus Structure
[Arbol de buses]

## File Formats
[Tabla type / format / sample rate / quality / mono-stereo]

## Folder Structure
[assets/audio/...]

## Godot Integration
- SFX playback
- Music manager

## Production Checklist
- Crear SFX
- Crear variaciones
- Componer music
- Definir loop points
- Exportar
- Organizar archivos
- Configurar buses
- Implementar playback
- Probar mix
```

## Validaciones finales

- SFX list cubre eventos del sistema
- Trigger names son claros
- Variaciones definidas para sonidos frecuentes
- Tracks con mood/tempo/instruments
- Loop points definidos
- Buses <= 10
- Formatos apropiados

## Cierre sugerido

- Produccion de audio
- `$godot-setup` para buses
- Implementacion de players y music manager
