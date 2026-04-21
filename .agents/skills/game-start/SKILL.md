---
name: game-start
description: >-
  Setup inicial de proyecto de juego 2D: detecta estado del proyecto, pregunta lenguaje
  (GDScript vs C#) y genero (RPG/platformer/roguelike), crea estructura de directorios,
  .gitignore para Godot. Usala cuando el usuario quiere iniciar un nuevo proyecto de juego
  2D con Godot, o cuando dice "nuevo juego", "empezar juego", "game-start", "setup
  proyecto".
---

# Game Start

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$game-start`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Si falta contexto menor, usa defaults practicos para Godot solo-dev y dejalos explicitos; pregunta solo antes de resetear o sobrescribir estructura existente.
- Delega solo si el usuario pidio paralelismo o delegacion.

Setup inicial de proyecto de juego 2D con Godot 4. Detectar estado, tomar decisiones de lenguaje y genero, crear estructura, guiar al siguiente paso.

## FASE 1: Detectar estado (silente)

Buscar `project.godot` y estructura existente (`src/`, `assets/`, `design/`, `production/`).

| Condicion | Accion |
|---|---|
| project.godot existe | Ya es proyecto Godot → preguntar completar o resetear |
| Estructura parcial | Preguntar completar o resetear |
| Directorio vacio | Setup completo |

PREGUNTAR antes de modificar si hay estructura existente.

## FASE 2: Elegir lenguaje

**GDScript** (recomendado para solo dev principiante gamedev):
- Hot reload, docs completas, menos verboso, menor memoria
- Desventaja: sin type safety fuerte (opcional desde GDScript 2.0)

**C#** (para devs con background C#/Java/Kotlin):
- Type safety, mejor performance en logic complejo, IDE con refactoring
- Desventaja: compilacion obligatoria, docs favorecen GDScript, mas verboso

## FASE 3: Elegir genero

Cada genero define que skills se usaran despues:

| Genero | Sistemas core | Skills principales | Scope MVP |
|--------|---------------|-------------------|-----------|
| RPG | Combate turnos, stats, inventario, dialogo | $rpg-design, $design-system | 20-40h |
| Platformer | Physics, collision, enemies, power-ups | $design-system, $level-brief | 15-30h |
| Roguelike | Procedural, permadeath, run progression | $rpg-design, $design-system | 30-50h |

## FASE 4: Crear estructura

```
project-root/
├─ src/{core,entities,systems,ui,utils}/
├─ assets/{sprites,tiles,audio/{music,sfx},data,fonts}/
├─ scenes/{levels,characters,ui,prefabs}/
├─ design/{gdd,levels}/
├─ production/sprints/
└─ tests/
```

## FASE 5: Crear .gitignore

Para Godot 4: `.godot/`, `.import/`, `builds/`, `.mono/`, `data_*/`, OS files, IDE files, Aseprite backups.

## FASE 6: Crear project.godot (si no existe)

Config minima con pixel-perfect settings:
- viewport 1280x720, stretch canvas_items, texture_filter 0 (Nearest)

## FASE 7: Crear primer sprint

Escribir `production/sprints/sprint-1.md` con objetivos iniciales: project settings, escena base, game loop, input map, player con movimiento basico, camera pixel-perfect.

Dependencies previas: `$game-concept`, `$art-bible`, al menos 1 sprite placeholder.

## FASE 8: Output summary

Resumen de lo creado: lenguaje, genero, estructura, archivos. Sugerir comando git add + commit.

## FASE 9: Siguiente paso

Opciones: `$game-concept`, `$art-bible`, `$brainstorm`. NO ejecutar automaticamente — esperar decision.

## Anti-patrones

- **Crear sin preguntar lenguaje/genero** → estructura generica sin guia
- **Sobreescribir sin confirmar** → perder trabajo existente
- **Estructura plana** → caos cuando el proyecto crece
- **No configurar pixel-perfect** → sprites borrosos, shimmer en scroll
