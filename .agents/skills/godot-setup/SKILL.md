---
name: godot-setup
description: >-
  Configura proyecto Godot 4 desde cero: detecta lenguaje (.gd vs .cs), define folder
  structure, configura autoloads (EventBus, managers), input actions, display settings, y
  export presets. Output: checklist de configuracion con valores concretos para
  project.godot y folder tree.
---

# Godot Project Setup

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$godot-setup`.
- Cuando aqui se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aqui se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario lo pidio explicitamente.
- Cuando un ejemplo heredado mencione tools de Claude, aplica la traduccion de `AGENTS.md` y expresa la accion con herramientas reales de Codex (`rg`, `find`, `sed -n`, shell puntual y patch nativo).

Configurar proyecto Godot 4: folder structure, autoloads, input map, display settings, export presets. Output: checklist de configuracion.

## FASE 1: Detectar proyecto y lenguaje

Buscar `project.godot` y contar archivos `.gd` vs `.cs`. Casos: proyecto existente (preguntar completar o resetear), proyecto nuevo (preguntar lenguaje).

**GDScript** (recomendado para solo dev): hot reload, docs completas, menos verboso.
**C#** (para devs C#/Java/Kotlin): type safety, mejor performance en logic pesado.

## FASE 2: Folder structure

```
project_root/
├─ src/                     # Scripts
│   ├─ gameplay/            # Player, enemies, items
│   ├─ core/                # State machine, resource pool
│   ├─ ui/                  # UI controllers
│   └─ autoloads/           # Singletons
├─ scenes/                  # .tscn files
│   ├─ levels/
│   ├─ characters/
│   ├─ ui/
│   └─ prefabs/
├─ assets/                  # Non-code
│   ├─ sprites/
│   ├─ tiles/
│   ├─ audio/{sfx,music,ambience}/
│   ├─ fonts/
│   ├─ data/                # JSON, CSV, resources
│   └─ shaders/
├─ design/                  # Design docs
├─ tests/                   # Unit tests (GUT)
└─ builds/                  # Export output (gitignored)
```

Reglas: src/ solo scripts, scenes/ solo .tscn, assets/ solo binarios.

Crear directorios. Crear `.gitignore` para Godot 4 (`.godot/`, `.import/`, `builds/`, `.mono/`).

## FASE 3: Autoloads

Leer `references/autoloads.md` para detalle completo de los autoloads base.

Set recomendado (4-6 max):
- **EventBus**: eventos globales desacoplados
- **GameManager**: flow y estado de alto nivel
- **SaveManager**: persistencia
- **AudioManager**: musica, SFX, buses

Reglas: single responsibility, si es scene-local no convertirlo en autoload.

Entregable: tabla `nombre → path → purpose`, bloque `[autoload]` para project.godot.

## FASE 4: Input actions

Definir por categoria: UI navigation (accept, cancel, arrows), player movement (WASD + gamepad stick), player actions (attack, interact, dodge, inventory), system (pause, fullscreen).

Tabla: `action → keys → gamepad → deadzone → type (digital/analog)`.

Incluir input actions completas para project.godot.

## FASE 5: Display settings (pixel art)

| Setting | Value | Razon |
|---------|-------|-------|
| Viewport | 320x180 | Internal resolution (16:9) |
| Window | 1280x720 | 4x integer scale |
| Stretch mode | canvas_items | Scales UI y sprites |
| Stretch aspect | keep | Mantiene aspect ratio |
| Scale mode | integer | Pixel-perfect (no blur) |
| Texture filter | 0 (Nearest) | Critico para pixel art |
| GPU pixel snap | true | Alinea sprites al grid |

## FASE 6: Export presets

Leer `references/export-presets.md` para presets concretos.

Regla: empezar con 1-2 presets (Windows baseline, HTML5 opcional). Excluir `design/`, `tests/`, markdown.

Entregable: tabla por preset + checklist de verificacion.

## FASE 7: Generar checklist

Leer `references/checklist-template.md` para estructura y validaciones finales.
