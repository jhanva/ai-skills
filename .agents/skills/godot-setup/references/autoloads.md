# Godot Setup — Autoload Reference

Lee este archivo solo cuando necesites definir o justificar autoloads concretos.

## Autoloads base recomendados

### EventBus
- Path: `res://src/autoloads/event_bus.gd`
- Rol: eventos globales desacoplados
- Usar para: HUD, game state changes, notificaciones cross-system

### GameManager
- Path: `res://src/autoloads/game_manager.gd`
- Rol: estado global de partida y flow de alto nivel
- Usar para: pause, scene flow, current run/session state

### SaveManager
- Path: `res://src/autoloads/save_manager.gd`
- Rol: save/load y persistencia
- Usar para: serializacion, checkpoints, ranuras

### AudioManager
- Path: `res://src/autoloads/audio_manager.gd`
- Rol: reproduccion de music/SFX y control de buses
- Usar para: play/stop track, one-shots globales, volumen

## Regla de tamano

- Mantener el set base en 4-6 autoloads
- Si aparecen mas de 6, justificar por que no son scene-local services

## Secciones de `project.godot` a tocar

- `[autoload]`
- `[input]`
- `[display]`
- `[rendering]`
