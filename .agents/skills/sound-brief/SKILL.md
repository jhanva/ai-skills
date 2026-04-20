---
name: sound-brief
description: >-
  Define audio brief para sistemas o zonas: lista de SFX con triggers, music brief (mood,
  tempo, instruments), audio bus structure, formatos, y Godot integration. Output:
  design/audio/{system}-brief.md con specs completas para produccion de audio.
---

# Sound Brief

Specs de audio para sistemas o zonas: SFX list, music brief, bus architecture, formatos, Godot integration. Output: `design/audio/{system}-brief.md`.

## FASE 1: Leer contexto

Leer `design/gdd/game-concept.md` para genero, mood, target, art style. Buscar documentacion del sistema especifico. Identificar eventos audiovisuales clave.

## FASE 2: Clasificar sistema

| Type | SFX Count | Music | Ejemplo |
|------|-----------|-------|---------|
| Combat | 15-30 | Combat theme (adaptive) | Attacks, hits, parry, death |
| UI/Menu | 8-15 | Menu theme (loop) | Click, hover, confirm, cancel |
| Zone/Biome | 20-40 | Ambient + exploration | Footsteps, ambience, wildlife |
| Puzzle | 10-20 | Puzzle theme (calm loop) | Move piece, correct, wrong, solve |
| Boss Fight | 20-35 | Boss theme (multi-phase) | Attacks, phase change, defeat |

## FASE 3: SFX list con triggers

Tabla: `trigger → description → duration → priority → variations → file`.

Reglas de priority:
- **High**: gameplay critico (attacks, hits) — nunca se dropea
- **Medium**: feedback importante (pickup, UI) — puede ser interrumpido
- **Low**: ambient (footsteps) — primero en ser culled

Reglas de variations: 1 para UI (consistencia), 2-3 para attacks/hits, 4-5 para footsteps (evitar repeticion).

Footsteps necesitan variations POR terrain type (grass, dirt, stone, wood).

## FASE 4: Music brief

Tabla: `track → mood → tempo (BPM) → instruments → duration → loop → adaptive`.

Tempo guidelines: 60-90 lento (ambient), 90-120 medio (exploration), 120-150 rapido (combat), 150-180 muy rapido (boss).

Especificar loop points (intro vs loop body) y adaptive behavior si aplica:
- **Layers**: add/remove instruments segun intensidad
- **Phases**: switch sections segun game state (calm/alert/combat)

## FASE 5: Audio bus structure

Hierarchy recomendada:

```
Master (0 dB, Limiter)
  ├─ SFX (-3 dB)
  │   ├─ Player SFX (0 dB)
  │   ├─ Enemy SFX (0 dB)
  │   ├─ Environment SFX (-6 dB, Reverb small)
  │   └─ UI SFX (+3 dB)
  ├─ Music (-6 dB)
  └─ Voice (0 dB) [future]
```

Reglas: SFX ligeramente mas bajo que music, UI SFX boosted para claridad, Environment SFX con reverb.

## FASE 6: Formatos de archivo

| Asset | Format | Sample Rate | Notes |
|-------|--------|-------------|-------|
| SFX corto (<3s) | WAV 16-bit | 44.1 kHz | Zero latency |
| SFX largo (>3s) | OGG Vorbis Q6 | 44.1 kHz | Compressed |
| Music | OGG Vorbis Q7 | 44.1 kHz | High quality |
| Ambience | OGG Vorbis Q5 | 44.1 kHz | Smaller filesize |

Naming: `{category}_{name}_{variation}.{ext}` (ej: `sfx_attack_light_01.wav`). Lowercase, underscore, zero-padded variation.

Folder structure: `assets/audio/{sfx/{player,enemy,environment,ui},music,ambience}/`.

## FASE 7: Godot integration

- **AudioStreamPlayer**: non-spatial (music, UI SFX)
- **AudioStreamPlayer2D**: spatial (footsteps, enemy sounds)
- **Random variations**: array de streams, `pick_random()` al play
- **Music manager** (autoload): crossfade con Tween al cambiar tracks

## FASE 8: Generar sound brief

Escribir `design/audio/{system}-brief.md`. Leer `references/output-template.md` para estructura, production checklist, y validaciones.
