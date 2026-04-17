---
name: sound-brief
description: >
  Define audio brief para sistemas o zonas: lista de SFX con triggers, music
  brief (mood, tempo, instruments), audio bus structure, formatos, y Godot
  integration. Output: design/audio/{system}-brief.md con specs completas
  para produccion de audio.
argument-hint: "<sistema o zona> (ej: combat, forest, menu)"
disable-model-invocation: true
agent: sound-designer
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
---

# Sound Brief

Define specs completas de audio para sistemas de juego o zonas: SFX list con triggers, music brief, audio bus architecture, formatos de archivo, y Godot integration. Genera brief tecnico para producir audio assets.

## FASE 1: Leer Game Concept y Contexto

**Objetivo**: Cargar informacion del sistema/zona para definir audio apropiado.

1. Buscar y leer `design/game-concept.md` o `design/GDD.md`
2. Extraer datos criticos:
   - Genero del juego (RPG, platformer, action, puzzle)
   - Mood general (dark, cheerful, tense, relaxing)
   - Target audience (kids, adults, core gamers)
   - Art style (pixel art, realistic, cartoon)
3. Buscar documentacion del sistema especifico:
   - Para "combat": `design/combat-system.md`
   - Para "forest": `design/levels/forest.md` o `design/world/forest.md`
   - Para "menu": `design/ui-flow.md`
4. Identificar eventos audiovisuales clave del sistema

**Validaciones**:
- Si no hay game concept: WARNING (brief sera generico)
- Si el sistema no tiene design doc: Buscar referencias en otros docs con Grep

---

## FASE 2: Clasificar Sistema y Determinar Scope

**Objetivo**: Identificar tipo de sistema para aplicar template de audio apropiado.

### Tipos de sistema

| Type | Scope | SFX Count | Music | Example |
|------|-------|-----------|-------|---------|
| Combat | Medium | 15-30 | Combat theme (adaptive) | Attacks, hits, parry, death |
| UI/Menu | Small | 8-15 | Menu theme (loop) | Click, hover, confirm, cancel |
| Zone/Biome | Large | 20-40 | Ambient + exploration theme | Footsteps, ambience, wildlife |
| Puzzle | Small | 10-20 | Puzzle theme (calm loop) | Move piece, correct, wrong, solve |
| Cutscene | Medium | 10-25 | Cinematic music (linear) | Dialog blips, transitions |
| Boss Fight | Medium | 20-35 | Boss theme (multi-phase) | Attacks, phase change, defeat |

### Templates de SFX por tipo

**Combat**:
- Player: Attack (light, heavy, special), hurt, death, footstep, dodge
- Enemy: Attack, hurt, death, spawn
- Impact: Hit flesh, hit armor, block, parry
- UI: HP low warning, level up

**UI/Menu**:
- Navigation: Hover, click, confirm, cancel, error
- Transitions: Open, close, slide in, slide out
- Feedback: Purchase, equip, save, achievement unlock

**Zone/Biome**:
- Ambience: Wind, birds, water flow (loopable)
- Player: Footsteps (grass, dirt, stone), jump, land
- Interactive: Door open/close, chest open, pickup item
- Wildlife: Animal sounds (distant, rare triggers)

**Puzzle**:
- Actions: Move piece, rotate, push block
- Feedback: Correct placement, wrong placement, undo
- Complete: Puzzle solved fanfare, door unlock

**Decision**: Determinar tipo de sistema y aplicar template correspondiente.

---

## FASE 3: Definir SFX List con Triggers

**Objetivo**: Tabla completa de sound effects con contexto de cuando se reproducen.

### Tabla de SFX

| Trigger | Description | Duration | Priority | Variations | File |
|---------|-------------|----------|----------|------------|------|
| player_attack_light | Sword swing (light attack) | 0.3s | High | 3 | sfx_attack_light_01.wav |
| player_attack_heavy | Sword swing (heavy attack) | 0.5s | High | 2 | sfx_attack_heavy_01.wav |
| enemy_hit | Impact when player hits enemy | 0.2s | High | 4 | sfx_hit_01.wav |
| enemy_death | Enemy defeated sound | 1.0s | Medium | 2 | sfx_enemy_death_01.wav |
| footstep_grass | Footstep en grass terrain | 0.15s | Low | 5 | sfx_footstep_grass_01.wav |
| chest_open | Chest opening | 0.8s | Medium | 1 | sfx_chest_open.wav |
| item_pickup | Pickup item/coin | 0.3s | High | 2 | sfx_pickup_01.wav |
| ui_confirm | Menu confirm button | 0.2s | Medium | 1 | sfx_ui_confirm.wav |
| ui_cancel | Menu cancel/back | 0.2s | Medium | 1 | sfx_ui_cancel.wav |

### Columnas explicadas

**Trigger**: Nombre descriptivo del evento que dispara el SFX (debe matchear con evento de codigo/animation)

**Description**: Descripcion clara del sonido y contexto

**Duration**: Duracion target del archivo de audio
- Short: 0.1-0.3s (impacts, clicks)
- Medium: 0.3-0.8s (actions, movements)
- Long: 0.8-2.0s (deaths, fanfares, transitions)

**Priority**: Importancia del sonido para mixing
- **High**: Gameplay critico (attacks, hits, jumps) — nunca se dropea
- **Medium**: Important feedback (item pickup, UI) — puede ser interrumpido por High
- **Low**: Ambient (footsteps, distant sounds) — primero en ser culled si hay voice limit

**Variations**: Cuantas versiones diferentes del mismo SFX
- 1: SFX unico, consistencia importante (UI sounds)
- 2-3: SFX importante con variacion (attacks, hits)
- 4-5: SFX frecuente, evitar repeticion (footsteps, impacts)

**File**: Naming convention del archivo de audio

### Reglas de SFX design

1. **Attacks**: Variations para evitar monotonia (minimo 2)
2. **Impacts**: Multiple variations (4-5) porque ocurren muy frecuentemente
3. **Footsteps**: Variations POR terrain type (grass, dirt, stone, wood)
4. **UI**: Consistencia (1 variation), sonidos iconicos
5. **Ambience**: Loopable, sin attacks obvios en el waveform

**Estimacion de SFX count**:
- Combat system: ~20-30 SFX
- UI system: ~10-15 SFX
- Zone: ~25-40 SFX (footsteps x terrain types + ambience + interactables)

**Output**: Tabla completa con TODOS los SFX necesarios para el sistema.

---

## FASE 4: Music Brief

**Objetivo**: Definir especificaciones de musica para el sistema/zona.

### Tabla de music tracks

| Track Name | Mood | Tempo | Instruments | Duration | Loop | Adaptive |
|------------|------|-------|-------------|----------|------|----------|
| Forest Exploration | Peaceful, wonder | 80 BPM | Flute, strings, harp | 2:30 | Yes | No |
| Combat Theme | Tense, energetic | 140 BPM | Drums, electric guitar, synth bass | 1:45 | Yes | Phase intro |
| Boss Theme | Epic, dangerous | 160 BPM | Orchestra, choir, drums | 3:00 | Yes | 3 phases |
| Menu Theme | Calm, inviting | 90 BPM | Piano, soft synth | 1:30 | Yes | No |

### Columnas explicadas

**Mood**: Emocion target del track (peaceful, tense, epic, melancholic, cheerful, mysterious)

**Tempo**: BPM (beats per minute)
- Slow: 60-90 BPM (ambient, sad, mysterious)
- Medium: 90-120 BPM (exploration, menu, casual)
- Fast: 120-150 BPM (action, combat, chase)
- Very fast: 150-180 BPM (boss fights, intense moments)

**Instruments**: Lista de instrumentos principales
- Orchestral: Strings, brass, woodwinds, percussion
- Synth: Lead synth, pad, bass, arp
- Guitar: Acoustic, electric, distorted
- Piano: Grand piano, electric piano
- Ethnic: Flute, shakuhachi, sitar, taiko drums
- Chiptune: Square wave, triangle, noise, pulse

**Duration**: Duracion del track completo antes de loop
- Short: 1:00-1:30 (menu, simple loops)
- Medium: 1:30-2:30 (exploration, standard combat)
- Long: 2:30-4:00 (boss fights, cinematic)

**Loop**: Si el track hace loop infinito (Yes) o es linear (No)

**Adaptive**: Si el track cambia segun gameplay
- No: Loop estatico
- Phase intro: Intro una vez, luego loop body
- Layers: Add/remove layers segun intensidad (combat start/end)
- Vertical: Switch sections segun game state (calm/alert/combat)
- Horizontal: Transition entre tracks suavemente

### Loop Points

Para tracks que hacen loop, especificar loop points:

```
Forest Exploration:
  - Intro: 0:00-0:15 (plays once)
  - Loop body: 0:15-2:30 (loops infinitely)
  - Loop point: 2:30 -> 0:15 (seamless transition)
```

### Adaptive Music Examples

**Combat (layers)**:
```
Layer 0 (always): Drums, bass (foundation)
Layer 1 (enemies spotted): Add melody, strings
Layer 2 (in combat): Add brass, increase intensity
Layer 3 (low HP): Add alarm synth, high-pass filter effect
```

**Boss (phases)**:
```
Phase 1 (100-70% HP): Standard boss theme
Phase 2 (70-30% HP): Add choir, increase tempo 10%
Phase 3 (<30% HP): Full orchestra, distortion, double-time drums
```

**Implementacion en Godot**: `AudioStreamPlayer` con multiples tracks, crossfade con `Tween`.

**Output**: Tabla de tracks + loop points + adaptive logic (si aplica).

---

## FASE 5: Audio Bus Structure

**Objetivo**: Definir mixing hierarchy para control de volumen y effects.

### Godot Audio Bus Architecture

```
Master (0 dB)
  ├─ SFX (-3 dB)
  │   ├─ Player SFX (0 dB)
  │   ├─ Enemy SFX (0 dB)
  │   ├─ Environment SFX (-6 dB)
  │   └─ UI SFX (+3 dB)
  ├─ Music (-6 dB)
  │   ├─ Exploration (0 dB)
  │   ├─ Combat (0 dB)
  │   └─ Ambient (0 dB)
  └─ Voice (0 dB) [future]
```

### Tabla de buses

| Bus Name | Parent | Volume | Effects | Purpose |
|----------|--------|--------|---------|---------|
| Master | - | 0 dB | Limiter | Root bus, global volume control |
| SFX | Master | -3 dB | - | All sound effects |
| Player SFX | SFX | 0 dB | - | Player actions (attacks, jumps) |
| Enemy SFX | SFX | 0 dB | - | Enemy actions |
| Environment SFX | SFX | -6 dB | Reverb (small) | Ambient sounds, footsteps |
| UI SFX | SFX | +3 dB | - | Menu sounds (boosted for clarity) |
| Music | Master | -6 dB | EQ (low-pass subtle) | All music tracks |
| Exploration | Music | 0 dB | - | Exploration themes |
| Combat | Music | 0 dB | - | Combat themes |
| Ambient | Music | 0 dB | Reverb (large) | Atmospheric ambient loops |

### Reglas de mixing

1. **Master**: Limiter para evitar clipping (threshold -0.3 dB)
2. **SFX**: Ligeramente mas bajo que musica para no opacar
3. **Player SFX**: Volumen normal (importancia alta)
4. **Environment SFX**: Mas bajo para no distraer (-6 dB)
5. **UI SFX**: Ligeramente mas alto para feedback claro (+3 dB)
6. **Music**: Mas bajo que SFX para que gameplay sounds sean prominentes (-6 dB)

### Effects recomendados

**Reverb** (Environment SFX, Ambient):
- Room Size: Small (0.3-0.5)
- Damping: 0.6
- Wet: 0.2-0.3
- Dry: 1.0

**Limiter** (Master):
- Threshold: -0.3 dB
- Ceiling: -0.1 dB

**EQ** (Music, opcional):
- Low-pass: Cortar frecuencias >12kHz (evita fatiga auditiva)

**Configuracion en Godot**:
```gdscript
# Set bus volumes via script
AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), -3)
AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), -6)
```

**Output**: Diagram de bus hierarchy + tabla de volumes y effects.

---

## FASE 6: Formatos de Archivo

**Objetivo**: Definir formatos de audio para diferentes tipos de assets.

### Reglas de formato

| Asset Type | Duration | Format | Sample Rate | Bit Depth | Notes |
|------------|----------|--------|-------------|-----------|-------|
| SFX (short) | <3s | WAV | 44.1 kHz | 16-bit | Sin compression, low latency |
| SFX (long) | >3s | OGG Vorbis | 44.1 kHz | Q6 (~192 kbps) | Compressed, acceptable latency |
| Music | Any | OGG Vorbis | 44.1 kHz | Q7 (~224 kbps) | Compressed, high quality |
| Ambience | Loop | OGG Vorbis | 44.1 kHz | Q5 (~160 kbps) | Compressed, smaller filesize |
| Voice | Any | OGG Vorbis | 22.05 kHz | Q5 (~160 kbps) | Mono, compressed |

### Razonamiento

**WAV para SFX cortos**:
- Pro: Zero decompression overhead, instant playback
- Con: Filesize grande (1 MB por minuto de stereo)
- Use: Impacts, clicks, jumps (reproducidos frecuentemente)

**OGG para musica y SFX largos**:
- Pro: 80-90% filesize reduction vs WAV
- Con: Decompression CPU cost (minimo en hardware moderno)
- Use: Music loops, ambient loops, cinematic SFX

**Mono vs Stereo**:
- Mono: Voice, algunos SFX (footsteps, impacts)
- Stereo: Music, ambient loops, spatial SFX

### Naming Convention

Pattern: `{category}_{name}_{variation}.{ext}`

Ejemplos:
- `sfx_attack_light_01.wav`
- `sfx_footstep_grass_03.wav`
- `music_forest_exploration.ogg`
- `amb_wind_loop.ogg`

**Reglas**:
- Lowercase, underscore separators
- Variation number con zero-padding (01, 02, ..., 10)
- Category prefix para organizar en filesystem

### Folder Structure

```
assets/audio/
  sfx/
    player/
      sfx_attack_light_01.wav
      sfx_attack_heavy_01.wav
      sfx_hurt_01.wav
    enemy/
      sfx_enemy_hit_01.wav
      sfx_enemy_death_01.wav
    environment/
      sfx_footstep_grass_01.wav
      sfx_chest_open.wav
    ui/
      sfx_ui_confirm.wav
      sfx_ui_cancel.wav
  music/
    music_forest_exploration.ogg
    music_combat_theme.ogg
    music_boss_theme.ogg
  ambience/
    amb_forest_wind.ogg
    amb_forest_birds.ogg
```

**Output**: Tabla de formatos + naming convention + folder structure.

---

## FASE 7: Godot Integration

**Objetivo**: Especificar como integrar los audio assets en Godot 4.

### AudioStreamPlayer Types

| Node | Use Case | Features | Example |
|------|----------|----------|---------|
| AudioStreamPlayer | Non-spatial audio | Global, no 3D position | Music, UI SFX |
| AudioStreamPlayer2D | 2D spatial audio | Panning based on position | Footsteps, enemy sounds |
| AudioStreamPlayer3D | 3D spatial audio | Distance attenuation, doppler | Not used en 2D games |

### Configuration para SFX

**Player attack SFX**:
```gdscript
# En script de player
@onready var attack_sound = $AttackSound  # AudioStreamPlayer2D

func _attack():
    # Random variation
    var sfx = [
        preload("res://assets/audio/sfx/player/sfx_attack_light_01.wav"),
        preload("res://assets/audio/sfx/player/sfx_attack_light_02.wav"),
        preload("res://assets/audio/sfx/player/sfx_attack_light_03.wav")
    ]
    attack_sound.stream = sfx.pick_random()
    attack_sound.play()
```

**UI click SFX**:
```gdscript
# En script de UI button
@onready var click_sound = $ClickSound  # AudioStreamPlayer (non-spatial)

func _on_button_pressed():
    click_sound.play()
```

### Configuration para Music

**Music manager (autoload)**:
```gdscript
extends Node

@onready var music_player = AudioStreamPlayer.new()
var current_track = ""

func _ready():
    add_child(music_player)
    music_player.bus = "Music"

func play_track(track_name: String, fade_duration: float = 1.0):
    if current_track == track_name:
        return
    
    var track = load("res://assets/audio/music/music_" + track_name + ".ogg")
    
    # Crossfade
    if music_player.playing:
        var tween = create_tween()
        tween.tween_property(music_player, "volume_db", -80, fade_duration)
        tween.tween_callback(func(): _switch_track(track))
    else:
        _switch_track(track)
    
    current_track = track_name

func _switch_track(track: AudioStream):
    music_player.stream = track
    music_player.play()
    var tween = create_tween()
    tween.tween_property(music_player, "volume_db", 0, 1.0)
```

**Uso**:
```gdscript
# Al entrar a zona forest
MusicManager.play_track("forest_exploration")

# Al iniciar combate
MusicManager.play_track("combat_theme")
```

### AudioStreamPlayer2D Settings

| Property | Value | Reason |
|----------|-------|--------|
| Max Distance | 1000-2000 | Cuanto lejos se escucha el sonido |
| Attenuation | 1.0-2.0 | Que tan rapido decae el volumen con distancia |
| Bus | "Player SFX" | Routing al bus correcto |
| Autoplay | false | Controlar playback desde script |

**Output**: Code snippets + tabla de settings.

---

## FASE 8: Generar Sound Brief Document

**Objetivo**: Escribir `design/audio/{system}-brief.md` completo.

### Template del documento

```markdown
# {System} Audio Brief

**System**: Combat
**Genre**: Action RPG
**Mood**: Tense, energetic
**Date**: 2026-04-17

## SFX List

| Trigger | Description | Duration | Priority | Variations | File |
|---------|-------------|----------|----------|------------|------|
| player_attack_light | Light sword swing | 0.3s | High | 3 | sfx_attack_light_01.wav |
| ... | ... | ... | ... | ... | ... |

**Total SFX**: 25

## Music Tracks

| Track Name | Mood | Tempo | Instruments | Duration | Loop | Adaptive |
|------------|------|-------|-------------|----------|------|----------|
| Combat Theme | Tense, energetic | 140 BPM | Drums, guitar, synth bass | 1:45 | Yes | Phase intro |

**Loop Points**:
- Intro: 0:00-0:10 (plays once)
- Body: 0:10-1:45 (loops infinitely)
- Loop point: 1:45 -> 0:10

## Audio Bus Structure

```
Master (0 dB)
  ├─ SFX (-3 dB)
  │   ├─ Player SFX (0 dB)
  │   └─ Enemy SFX (0 dB)
  └─ Music (-6 dB)
```

## File Formats

| Type | Format | Sample Rate | Quality | Mono/Stereo |
|------|--------|-------------|---------|-------------|
| SFX <3s | WAV | 44.1 kHz | 16-bit | Mono |
| Music | OGG | 44.1 kHz | Q7 (224 kbps) | Stereo |

## Folder Structure

```
assets/audio/
  sfx/
    player/
    enemy/
  music/
```

## Godot Integration

**SFX Playback**:
```gdscript
@onready var attack_sound = $AttackSound
attack_sound.stream = preload("res://assets/audio/sfx/player/sfx_attack_light_01.wav")
attack_sound.play()
```

**Music Manager**:
Use autoload `MusicManager.play_track("combat_theme")`

## Production Checklist

- [ ] Record/synthesize all SFX (25 total)
- [ ] Create variations (3 for attacks, 4 for impacts)
- [ ] Compose combat theme (140 BPM, 1:45 duration)
- [ ] Set loop points en DAW (0:10-1:45)
- [ ] Export SFX as WAV 44.1kHz 16-bit mono
- [ ] Export music as OGG Q7 stereo
- [ ] Organize files en folder structure
- [ ] Configure audio buses en Godot
- [ ] Implement AudioStreamPlayer nodes
- [ ] Test playback en game
- [ ] Balance volumes (mixing pass)
```

**Accion**: Escribir archivo completo con datos de todas las fases.

---

## FASE 9: Validaciones Finales

**Checklist**:

- [ ] SFX list cubre todos los eventos audiovisuales del sistema
- [ ] Cada SFX tiene trigger name claro (matchea con codigo/animation)
- [ ] Variations estan definidas para SFX frecuentes
- [ ] Music tracks tienen mood, tempo, instruments especificados
- [ ] Loop points estan definidos para tracks que hacen loop
- [ ] Audio bus structure tiene <= 10 buses (no over-complicate)
- [ ] Formatos de archivo son apropiados (WAV para short SFX, OGG para music)
- [ ] Godot integration tiene code examples concretos
- [ ] Document incluye production checklist

**Warnings**:
- Si SFX count > 50: Sistema muy complejo, considerar split
- Si music tracks > 5: Mucha produccion musical, priorizar
- Si buses > 10: Over-engineering, simplificar

**Output final**: Path absoluto del archivo generado.

---

## Transicion al Siguiente Paso

Una vez completado el brief:

1. **Siguiente**: Produccion de audio (grabacion/sintesis de SFX, composicion de musica)
2. **Tools**: DAW (Reaper, FL Studio, Ableton), SFX tools (BFXR, ChipTone para chiptune)
3. **Despues**: `/godot-setup` para configurar audio buses en proyecto
4. **Finalmente**: Implementar AudioStreamPlayer nodes y music manager

**Entregable**: `design/audio/{system}-brief.md` con specs completas de audio para produccion.
