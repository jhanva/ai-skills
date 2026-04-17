---
name: game-start
description: >
  Setup inicial de proyecto de juego 2D: detecta estado del proyecto,
  pregunta lenguaje (GDScript vs C#) y genero (RPG/platformer/roguelike),
  crea estructura de directorios, .gitignore para Godot.
when_to_use: >
  Cuando el usuario quiere iniciar un nuevo proyecto de juego 2D con Godot,
  o cuando dice "nuevo juego", "empezar juego", "game-start", "setup proyecto".
argument-hint: "[no arguments]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
  - Bash(mkdir *)
  - Bash(ls *)
---

# Game Start — Setup inicial de proyecto de juego 2D

## Objetivo

Configurar la estructura base de un proyecto de juego 2D con Godot 4.
Detectar estado actual, tomar decisiones de lenguaje y genero, crear
directorios, archivos de configuracion, y guiar al siguiente paso.

---

## FASE 1: Detectar estado del proyecto (SILENTE)

NO preguntar al usuario todavia. Detectar automaticamente:

```bash
# Buscar archivos .godot o project.godot
find . -name "project.godot" -o -name ".godot"

# Buscar estructura existente
ls -la src/ assets/ design/ production/ tests/ 2>/dev/null
```

**Casos:**

| Condicion | Accion |
|---|---|
| `project.godot` existe | Ya es proyecto Godot → preguntar si resetear estructura |
| `src/` o `assets/` existen | Estructura parcial → preguntar si completar o resetear |
| Directorio vacio | Proyecto nuevo → continuar con setup completo |

Si el proyecto ya tiene estructura, PREGUNTAR antes de modificar:

```
Detecte estructura existente:
  [x] project.godot
  [x] src/
  [ ] design/
  [ ] production/

¿Que quieres hacer?
a) Completar directorios faltantes (conservar existentes)
b) Resetear todo (borrar y recrear desde cero)
c) Cancelar (no modificar nada)
```

---

## FASE 2: Elegir lenguaje de programacion

Presentar opciones con tradeoffs CLAROS:

```
## Lenguaje para Godot 4

Godot 4 soporta GDScript (nativo) y C# (via Mono/.NET).

### Opcion A: GDScript
- Lenguaje: Python-like, dinamico, integrado con Godot
- Ventajas:
  * Hot reload instantaneo (editas y pruebas sin recompilar)
  * Documentacion oficial mas completa
  * Menos verboso, desarrollo mas rapido
  * Menor consumo de memoria
- Desventajas:
  * Sin type safety fuerte (opcional desde GDScript 2.0)
  * Performance ~10-20% menor que C# en logic pesado
  * No compartir codigo con proyectos .NET/Unity
- Mejor para: solo dev, prototipado rapido, juegos 2D no intensivos

### Opcion B: C#
- Lenguaje: C# 10+, estatico, compilado
- Ventajas:
  * Type safety fuerte, menos bugs en runtime
  * Mejor performance en logic complejo (AI, pathfinding)
  * Familiaridad si vienes de Android/Kotlin (similares)
  * IDE: Rider/VS tienen mejor refactoring que script editor
- Desventajas:
  * Compilacion obligatoria (no hot reload, slower iteration)
  * Documentacion oficial favorece GDScript (adaptar ejemplos)
  * Mas verboso (boilerplate de clases, namespaces)
  * Godot Mono build requerido (binario mas pesado)
- Mejor para: devs con background C#/Java/Kotlin, proyectos grandes

¿Que lenguaje usaras?
a) GDScript (recomendado para solo dev + principiante gamedev)
b) C#
```

Guardar decision en variable interna: `LANGUAGE = "gdscript" | "csharp"`

---

## FASE 3: Elegir genero del juego

Presentar opciones con implicaciones de scope:

```
## Genero del juego

Cada genero tiene sistemas core diferentes. Esto define que skills
usaras mas adelante.

### Opcion A: RPG (2D pixel art)
- Sistemas core: combate por turnos, stats, inventario, dialogo
- Skills principales: /rpg-design, /design-system (dialogo/inventario)
- Scope tipico: 20-40 horas de desarrollo para MVP
- Ejemplo: clasico JRPG estilo SNES (Final Fantasy, Chrono Trigger)

### Opcion B: Platformer (2D pixel art)
- Sistemas core: physics, collision, enemies, power-ups
- Skills principales: /design-system (movement/abilities), /level-brief
- Scope tipico: 15-30 horas de desarrollo para MVP
- Ejemplo: Celeste, Shovel Knight, Hollow Knight (2D seccion)

### Opcion C: Roguelike (2D pixel art)
- Sistemas core: procedural generation, permadeath, run progression
- Skills principales: /rpg-design (combat), /design-system (generation)
- Scope tipico: 30-50 horas de desarrollo para MVP
- Ejemplo: Hades (2D), Enter the Gungeon, Dead Cells

### Opcion D: Otro (especifica)
- Describir: genero, mecanicas core, referencia

¿Que genero?
a) RPG
b) Platformer
c) Roguelike
d) Otro: ___
```

Guardar decision: `GENRE = "rpg" | "platformer" | "roguelike" | "<custom>"`

---

## FASE 4: Crear estructura de directorios

Estructura unificada para TODOS los generos:

```
project-root/
├── src/                      # codigo fuente (GDScript o C#)
│   ├── core/                 # game loop, state machine, managers
│   ├── entities/             # player, enemies, NPCs
│   ├── systems/              # combat, dialogue, inventory (segun genero)
│   ├── ui/                   # menus, HUD, dialogos
│   └── utils/                # helpers, extensions
├── assets/                   # recursos del juego
│   ├── sprites/              # sprite sheets (characters, enemies, items)
│   ├── tiles/                # tilesets (terrain, buildings, decorations)
│   ├── audio/                # musica y SFX
│   │   ├── music/
│   │   └── sfx/
│   ├── data/                 # archivos de datos (JSON, CSV)
│   │   ├── enemies.json
│   │   ├── items.json
│   │   ├── skills.json
│   │   └── levels.json
│   └── fonts/                # fuentes bitmap
├── design/                   # documentacion de diseno
│   ├── gdd/                  # game design documents
│   │   └── game-concept.md   (creado por /game-concept)
│   ├── levels/               # level briefs
│   └── art-bible.md          (creado por /art-bible)
├── production/               # project management
│   └── sprints/              # sprints y tasks
│       └── sprint-1.md
└── tests/                    # tests unitarios (GDScript o C#)
    └── test_*.gd / test_*.cs
```

Ejecutar:

```bash
mkdir -p src/{core,entities,systems,ui,utils}
mkdir -p assets/{sprites,tiles,audio/{music,sfx},data,fonts}
mkdir -p design/{gdd,levels}
mkdir -p production/sprints
mkdir -p tests
```

Si `LANGUAGE == "csharp"`, tambien crear:

```bash
mkdir -p src/.csproj  # placeholder para proyecto C#
```

---

## FASE 5: Crear .gitignore para Godot

Escribir `.gitignore` en la raiz del proyecto:

```gitignore
# Godot 4.x
.godot/
.import/
export.cfg
export_presets.cfg

# Godot auto-generated files
*.translation

# Mono / C#
.mono/
data_*/
mono_crash.*.json
.vs/
.vscode/
*.csproj
*.sln
*.user
*.suo

# Build outputs
builds/
exports/

# OS
.DS_Store
Thumbs.db
*.swp
*.swo
*~

# IDE
.idea/
*.iml

# Aseprite backups
*.aseprite~

# Temp files
*.tmp
*.log
```

---

## FASE 6: Crear archivo de proyecto inicial (opcional)

Si NO existe `project.godot`, crear uno minimo:

```ini
[application]
config/name="New Game"
config/features=PackedStringArray("4.3")

[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/size/mode=2
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"

[rendering]
textures/canvas_textures/default_texture_filter=0
```

Explicar configuracion:

| Setting | Valor | Por que |
|---|---|---|
| viewport_width/height | 1280x720 | Base resolution (16:9) |
| mode | 2 | Fullscreen |
| stretch/mode | canvas_items | Mantener pixel art sin blur |
| texture_filter | 0 | Nearest (critico para pixel art) |

---

## FASE 7: Crear primer sprint

Escribir `production/sprints/sprint-1.md`:

```markdown
# Sprint 1 — Setup & Core Systems

## Objetivos
- [ ] Configurar Godot project settings
- [ ] Crear escena base (Main.tscn)
- [ ] Implementar game loop basico
- [ ] Configurar input map (movement, confirm, cancel)
- [ ] Crear player entity con movimiento basico
- [ ] Setup de camara con pixel-perfect snapping

## Dependencias previas
- Definir game concept (`/game-concept`)
- Definir art bible (`/art-bible`)
- Tener al menos 1 sprite placeholder del player

## Siguientes pasos
- Sprint 2: Core systems del genero (combate/physics/generation segun genero)
```

---

## FASE 8: Output summary

Presentar resumen de lo creado:

```
## Setup completado

Lenguaje: [GDScript | C#]
Genero: [RPG | Platformer | Roguelike | <custom>]

Estructura creada:
  ✓ src/           (codigo fuente organizado por responsabilidad)
  ✓ assets/        (sprites, tiles, audio, data, fonts)
  ✓ design/        (GDDs y level briefs)
  ✓ production/    (sprints)
  ✓ tests/         (tests unitarios)
  ✓ .gitignore     (Godot 4 + Mono + OS)
  ✓ project.godot  (pixel art settings)
  ✓ sprint-1.md    (primeras tareas)

Archivos listos para git:
  git add .gitignore project.godot production/sprints/sprint-1.md
  git commit -m "chore: initial game project setup

  - Language: [GDScript|C#]
  - Genre: [RPG|Platformer|Roguelike]
  - Directory structure for code, assets, design, and production
  - Godot 4 project with pixel-perfect settings

  Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## FASE 9: Sugerir siguiente paso

Dependiendo del genero:

```
## Siguientes pasos recomendados

### Paso 1: Definir concepto del juego
Usa `/game-concept` para definir los 3 pillars, core loop, mecanicas MVP,
y look & feel del juego. Esto produce `design/gdd/game-concept.md`.

### Paso 2: Definir art bible (en paralelo o despues)
Usa `/art-bible` para definir resolucion, paleta, estilo de sprites,
y reglas de animacion. Esto produce `design/art-bible.md`.

### Alternativa: Brainstorming libre
Si prefieres explorar ideas primero, usa `/brainstorm` para un proceso
de diseno guiado con preguntas socraticas.

¿Que hacemos ahora?
a) /game-concept (definir concepto y mecanicas)
b) /art-bible (definir estetica y assets)
c) /brainstorm (explorar ideas libremente)
d) Otra cosa (especifica)
```

NO ejecutar automaticamente el siguiente paso. Esperar decision del usuario.

---

## Anti-patrones

```
ANTI-PATRON: Crear proyecto sin preguntar lenguaje/genero
  → Estructura generica sin guia de siguientes pasos
  Solucion: siempre preguntar, las decisiones afectan skills posteriores

ANTI-PATRON: Sobreescribir archivos sin confirmar
  → Perder trabajo existente
  Solucion: detectar estado en FASE 1 y confirmar antes de modificar

ANTI-PATRON: Crear .godot/ o archivos auto-generados
  → Ruido en git, conflictos innecesarios
  Solucion: .gitignore creado en FASE 5 los excluye

ANTI-PATRON: Estructura plana (todo en raiz)
  → Caos cuando el proyecto crece
  Solucion: estructura jerarquica desde dia 1

ANTI-PATRON: No configurar pixel-perfect settings
  → Sprites borrosos, shimmer en scroll
  Solucion: texture_filter=0, stretch mode canvas_items
```

## Argumento: $ARGUMENTS
