<div align="center">

# ai-skills

Convierte un repositorio en un stack de desarrollo asistido por IA con skills, agentes y reglas reutilizables.

**39 skills. 13 agentes de Codex. 5 hooks de Claude. Dos runtimes, un mismo workflow.**

[![Skills](https://img.shields.io/badge/skills-39-84cc16?style=for-the-badge)](#skills)
[![Codex Agents](https://img.shields.io/badge/codex%20agents-13-8b5cf6?style=for-the-badge)](#agentes)
[![Claude Hooks](https://img.shields.io/badge/claude%20hooks-5-f97316?style=for-the-badge)](#hooks-game-dev-capa-claude)
[![Runtimes](https://img.shields.io/badge/runtimes-2-0ea5e9?style=for-the-badge)](#compatibilidad-por-runtime)
[![Game Dev](https://img.shields.io/badge/game%20dev-20%20skills-ec4899?style=for-the-badge)](#game-development)

[Ver skills](#skills) • [Ver agentes](#agentes) • [Ver flujos](#flujos-de-trabajo) • [Ver compatibilidad](#compatibilidad-por-runtime)

</div>

Skills y agentes especializados para imponer flujos de desarrollo disciplinados: TDD, debugging sistematico, diseno antes de implementacion, seguridad y verificacion con evidencia.

El repositorio mantiene dos adaptaciones paralelas de esas mismas capacidades:

- `.claude/` conserva la implementacion original para Claude Code
- `.agents/skills/`, `.codex/agents/` y `.codex/config.toml` contienen la adaptacion nativa para Codex

Invocacion explicita por runtime:

- Codex: `$skill`
- Claude Code: `/skill`

En este README, las tablas se enfocan primero en la capacidad que aporta cada skill. Los detalles de runtime aparecen solo cuando cambian la invocacion o la integracion.

## Navegacion rapida

- [Que incluye](#que-incluye)
- [Skills Core](#core-desarrollo-general)
- [Skills Android](#android)
- [Skills Windows / Repo Ops](#windows--repo-ops)
- [Skills de Imagen](#imagen)
- [Skills de Game Development](#game-development)
- [Agentes](#agentes)
- [Plugins](#plugins)
- [Flujos de trabajo](#flujos-de-trabajo)
- [Compatibilidad por runtime](#compatibilidad-por-runtime)
- [Instalacion](#instalacion)
- [Estructura](#estructura)

## Que incluye

| Categoria | Cantidad | Descripcion |
|---|---:|---|
| Skills | 39 | Workflows para desarrollo general, Android, imagen, game dev, texto y operaciones de repo |
| Agentes Codex | 13 | Especialistas para implementacion, review, seguridad, prompt design y game development |
| Plugins Codex | 1 | Integracion local instalable para Aseprite via plugin + MCP |
| Hooks Claude | 5 | Validaciones automaticas para codigo, assets y contexto de sesion |
| Biblioteca compartida | 1 | `_parse.sh` para utilidades reutilizadas por hooks de Claude |
| Runtimes | 2 | Mismas capacidades adaptadas a Claude Code y Codex |

## Skills

### Core (desarrollo general)

| Skill | Activacion | Proposito |
|---|---|---|
| [`optimize`](./.agents/skills/optimize/SKILL.md) | Base del repo | Filtrado de output, umbral de delegacion y seleccion de modelo; complementa las reglas globales de eficiencia |
| [`brainstorm`](./.agents/skills/brainstorm/SKILL.md) | Explicita | Diseno antes de implementar. Dialogo socratico, multiples enfoques, spec escrita |
| [`plan`](./.agents/skills/plan/SKILL.md) | Explicita | Convertir spec aprobada en plan de implementacion con tareas de 2-5 min |
| [`tdd`](./.agents/skills/tdd/SKILL.md) | Contextual + explicita | Test-driven development estricto. Ciclo RED-GREEN-REFACTOR obligatorio |
| [`debug`](./.agents/skills/debug/SKILL.md) | Contextual + explicita | Debugging sistematico en 4 fases con investigacion de causa raiz |
| [`verify`](./.agents/skills/verify/SKILL.md) | Contextual + explicita | Verificacion con evidencia antes de cualquier claim de exito |
| [`execute`](./.agents/skills/execute/SKILL.md) | Explicita | Ejecucion de plan con revision de 2 etapas; delegacion solo cuando aplica |
| [`review`](./.agents/skills/review/SKILL.md) | Explicita | Code review estructurado con severidades |
| [`parallel`](./.agents/skills/parallel/SKILL.md) | Explicita | Despachar agentes paralelos para problemas independientes |
| [`secure`](./.agents/skills/secure/SKILL.md) | Explicita | Analisis de seguridad: secrets, injection, auth, crypto, infra. Modo quick o full |

### Android

| Skill | Activacion | Proposito |
|---|---|---|
| [`android-arch`](./.agents/skills/android-arch/SKILL.md) | Explicita | Validacion de boundaries de Clean Architecture Android |
| [`bitmap-safety`](./.agents/skills/bitmap-safety/SKILL.md) | Explicita | Auditoria de pipelines de procesamiento de imagen (memory, threading, errors) |
| [`room-audit`](./.agents/skills/room-audit/SKILL.md) | Explicita | Auditoria de seguridad de datos con Room (migraciones, schema, data safety) |

### Windows / Repo Ops

| Skill | Activacion | Proposito |
|---|---|---|
| [`windows-symlink`](./.agents/skills/windows-symlink/SKILL.md) | Explicita | Audita, habilita y repara soporte de symlinks en Windows para Git y checkouts del repo |

### Imagen

| Skill | Activacion | Proposito |
|---|---|---|
| [`image-algo`](./.agents/skills/image-algo/SKILL.md) | Explicita | Diseno de algoritmos de imagen (hashing, similarity, clustering) |
| [`ml-ondevice`](./.agents/skills/ml-ondevice/SKILL.md) | Explicita | Integracion de modelos ML on-device en Android |
| [`image-pipeline`](./.agents/skills/image-pipeline/SKILL.md) | Explicita | Diseno de pipelines de procesamiento de imagen multi-paso |

### Game development

Stack orientado a juegos 2D pixel art (RPG, platformer, roguelike) con Godot 4, GDScript y C#. Incluye 20 skills y 9 agentes especializados.

#### Onboarding

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`game-start`](./.agents/skills/game-start/SKILL.md) | Explicita | — | Setup guiado: Godot config, estructura de proyecto, GDScript vs C# |

#### Concepto

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`game-concept`](./.agents/skills/game-concept/SKILL.md) | Explicita | [`game-designer`](./.codex/agents/game-designer.toml) | Formalizar idea en concept doc (genero, pillars, target audience) |
| [`art-bible`](./.agents/skills/art-bible/SKILL.md) | Explicita | [`pixel-artist`](./.codex/agents/pixel-artist.toml) + [`creative-director`](./.codex/agents/creative-director.toml) | Identidad visual: paleta, estilo, resoluciones, restricciones |

#### Diseno

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`rpg-design`](./.agents/skills/rpg-design/SKILL.md) | Explicita | [`game-designer`](./.codex/agents/game-designer.toml) | Sistemas RPG (stats, formulas, turnos, balance, enemy AI) |
| [`design-system`](./.agents/skills/design-system/SKILL.md) | Explicita | [`game-designer`](./.codex/agents/game-designer.toml) | GDD para un sistema especifico (inventario, dialog, crafting) |
| [`level-brief`](./.agents/skills/level-brief/SKILL.md) | Explicita | [`level-designer`](./.codex/agents/level-designer.toml) | Disenar nivel: layout, encounters, curva de dificultad, pacing |
| [`balance-check`](./.agents/skills/balance-check/SKILL.md) | Contextual + explicita | [`game-designer`](./.codex/agents/game-designer.toml) | Validar balance numerico (damage curves, economy sinks/faucets) |

#### Arte y assets

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`pixel-pipeline`](./.agents/skills/pixel-pipeline/SKILL.md) | Explicita | [`pixel-artist`](./.codex/agents/pixel-artist.toml) | Pipeline completo de pixel art (sprites, tiles, atlas, palette swap) |
| [`sprite-spec`](./.agents/skills/sprite-spec/SKILL.md) | Explicita | [`pixel-artist`](./.codex/agents/pixel-artist.toml) | Spec de sprite sheet: frames, estados, dimensiones, hitbox |
| [`tileset-spec`](./.agents/skills/tileset-spec/SKILL.md) | Explicita | [`pixel-artist`](./.codex/agents/pixel-artist.toml) | Spec de tileset: tile size, autotile rules, variantes |
| [`palette`](./.agents/skills/palette/SKILL.md) | Explicita | [`pixel-artist`](./.codex/agents/pixel-artist.toml) | Crear/gestionar paletas de color (ramps, restrictions) |
| [`sound-brief`](./.agents/skills/sound-brief/SKILL.md) | Explicita | [`sound-designer`](./.codex/agents/sound-designer.toml) | Brief de audio: SFX list, mood board musical, integracion Godot |

#### Arquitectura

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`game-arch`](./.agents/skills/game-arch/SKILL.md) | Explicita | [`godot-architect`](./.codex/agents/godot-architect.toml) | Arquitectura de juegos 2D (game loop, FSM, commands, save system) |
| [`godot-setup`](./.agents/skills/godot-setup/SKILL.md) | Explicita | [`godot-architect`](./.codex/agents/godot-architect.toml) | Config proyecto Godot: autoloads, input map, export, folder structure |
| [`scene-design`](./.agents/skills/scene-design/SKILL.md) | Explicita | [`godot-architect`](./.codex/agents/godot-architect.toml) | Disenar escena: node tree, signals, script responsibilities |

#### Produccion

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`sprint`](./.agents/skills/sprint/SKILL.md) | Explicita | [`producer`](./.codex/agents/producer.toml) | Planificar sprint: stories, estimacion, prioridades |
| [`story`](./.agents/skills/story/SKILL.md) | Explicita | [`producer`](./.codex/agents/producer.toml) | Crear dev story desde seccion de GDD |
| [`scope-check`](./.agents/skills/scope-check/SKILL.md) | Contextual + explicita | [`producer`](./.codex/agents/producer.toml) | Verificar que el scope es realista vs tiempo disponible |

#### QA

| Skill | Activacion | Agente | Proposito |
|---|---|---|---|
| [`playtest`](./.agents/skills/playtest/SKILL.md) | Explicita | [`qa-analyst`](./.codex/agents/qa-analyst.toml) | Reporte estructurado de playtest session |
| [`smoke-test`](./.agents/skills/smoke-test/SKILL.md) | Explicita | [`qa-analyst`](./.codex/agents/qa-analyst.toml) | Checklist rapido pre-merge/pre-release |

### Texto

| Skill | Activacion | Proposito |
|---|---|---|
| [`humanize`](./.agents/skills/humanize/SKILL.md) | Explicita | Humanizar texto generado por IA: diagnostico (`review`) y reescritura (`rewrite`) |

**Base del repo** = principios globales que el runtime carga como contexto base; algunas capas ademas ofrecen una skill complementaria de referencia.
**Explicita** = se invoca por nombre cuando el usuario la necesita.
**Contextual + explicita** = puede activarse por el tipo de tarea y tambien invocarse directamente.

## Agentes

### Generales

| Agente | Proposito |
|---|---|
| [`prompt-artist`](./.codex/agents/prompt-artist.toml) | Transforma ideas en prompts narrativos optimizados para generacion de imagenes (Gemini, DALL-E, Midjourney, Stable Diffusion). Formula de 7 componentes con pesos por dominio |

### Game dev — Jerarquia de estudio

9 agentes organizados en 2 niveles para concepto, arte, arquitectura, produccion y QA. La implementacion concreta depende del runtime; en Codex viven en `.codex/agents/`.

```
Tier 1 — Directores
  creative-director ──── pixel-artist
    (vision, coherencia       sound-designer
     arte + diseno)           game-designer
                              level-designer

  technical-director ─── godot-architect
    (arquitectura,            qa-analyst
     codigo + calidad)        producer
```

| Agente | Tier | Dominio | Se activa cuando... |
|---|---|---|---|
| [`creative-director`](./.codex/agents/creative-director.toml) | Director | Vision global, coherencia arte/diseno | Conflicto entre dominios creativos, review de concepto |
| [`technical-director`](./.codex/agents/technical-director.toml) | Director | Arquitectura global, performance | Conflicto codigo/performance, decision arquitectural |
| [`pixel-artist`](./.codex/agents/pixel-artist.toml) | Especialista | Sprites, tiles, animacion, paletas, atlas | Editando `assets/sprites/`, `assets/tiles/` |
| [`sound-designer`](./.codex/agents/sound-designer.toml) | Especialista | SFX, musica, audio pipeline | Editando `assets/audio/`, definiendo audio en GDD |
| [`game-designer`](./.codex/agents/game-designer.toml) | Especialista | Sistemas, mecanicas, balance, economia | Escribiendo GDDs en `design/`, discutiendo mecanicas |
| [`level-designer`](./.codex/agents/level-designer.toml) | Especialista | Niveles, encounters, dificultad, world building | Editando `design/levels/`, discutiendo layout |
| [`godot-architect`](./.codex/agents/godot-architect.toml) | Especialista | Escenas, signals, GDScript/C#, patterns Godot | Editando `.gd`, `.cs`, `.tscn`, `.tres` |
| [`qa-analyst`](./.codex/agents/qa-analyst.toml) | Especialista | Tests, bug triage, playtesting | Post-implementacion, pre-release |
| [`producer`](./.codex/agents/producer.toml) | Especialista | Sprints, scope, milestones, stories | Planificando trabajo, revisando progreso |

## Hooks (game dev, capa Claude)

5 hooks de validacion automatica para codigo, assets y seguridad. Comparten biblioteca `_parse.sh` para parsing JSON (cero duplicacion).

| Hook | Evento | Que valida |
|---|---|---|
| [`block-env-access.sh`](./.claude/hooks/block-env-access.sh) | PreToolUse (Bash) | Bloquea lectura/escritura/source de archivos `.env` (permite `.env.example`, `.env.sample`, `.env.template`) |
| [`validate-gameplay-code.sh`](./.claude/hooks/validate-gameplay-code.sh) | PreToolUse (git commit) | No hardcoded values en `src/gameplay/`, delta time usage, no imports de UI en gameplay |
| [`validate-assets.sh`](./.claude/hooks/validate-assets.sh) | PostToolUse (Write/Edit) | Naming convention en `assets/` (lowercase_snake), JSON valido en data files |
| [`check-design-coverage.sh`](./.claude/hooks/check-design-coverage.sh) | PostToolUse (Write/Edit) | Advierte si existe codigo en `src/gameplay/X/` sin su `design/gdd/X.md` correspondiente |
| [`session-context.sh`](./.claude/hooks/session-context.sh) | SessionStart | Muestra branch, sprint activo, archivos modificados sin commit |

## Comandos

| Comando | Proposito |
|---|---|
| [`git-identity`](./.agents/skills/git-identity/SKILL.md) | Auditoria de cuentas git (4 capas: includeIf, shell guards, pre-commit hook, SSH keys) |
| [`git-identity setup`](./.agents/skills/git-identity/SKILL.md) | Configurar separacion de cuentas (macOS/Linux/Windows, mismo host o hosts diferentes) |

## Plugins

| Plugin | Ruta | Proposito |
|---|---|---|
| [`aseprite-codex`](./plugins/aseprite-codex/.codex-plugin/plugin.json) | `plugins/aseprite-codex/` | Integracion local para Aseprite con `skill` + `MCP` para inspeccionar sprites, exportar sprite sheets y correr scripts Lua desde Codex |

## Flujos de trabajo

### Desarrollo general

```
brainstorm  -->  plan  -->  execute (usa tdd internamente)
                                  |
                              review  -->  verify  -->  merge
```

### Debugging

```
debug  -->  tdd (para el fix)  -->  verify
```

### Features de imagen

```
image-algo     -->  image-pipeline  -->  plan  -->  execute
  (algoritmo)       (arquitectura)       (tareas)    (implementar)

ml-ondevice    -->  image-pipeline  -->  plan  -->  execute
  (modelo ML)       (arquitectura)       (tareas)    (implementar)
```

### Game development

```
Concepto:
  brainstorm  -->  game-concept  -->  art-bible
                         |
Diseno:                  |
  design-system  -->  rpg-design     -->  balance-check
  level-brief                                  |
                                                v
Arte:                                    Arquitectura:
  palette  -->  pixel-pipeline           game-arch  -->  godot-setup
  sprite-spec   tileset-spec             scene-design
  sound-brief                                  |
                                                v
Produccion:                              QA:
  sprint  -->  story  -->  plan         playtest  -->  smoke-test
                  |
                  v
            execute (usa tdd)  -->  review  -->  verify
```

Integracion con skills generales: `tdd` para todo codigo, `debug` para bugs, `verify` antes de completar, `review` para code review de GDScript/C#.

### Auditorias

```
android-arch    (boundaries de Clean Architecture)
bitmap-safety   (memory, threading, error handling de imagen)
room-audit      (migraciones, schema, data safety)
secure quick    (solo archivos cambiados, antes de commit/PR)
secure full     (proyecto completo, antes de deploy/release)
```

### Texto

```
humanize review [archivo]    (diagnostico sin modificar)
humanize rewrite [archivo]   (reescritura completa)
```

### Multiples problemas independientes

```
parallel  -->  verify
```

## Compatibilidad por runtime

- Claude Code: usa `.claude/skills/`, `.claude/agents/`, `.claude/commands/` y hooks. La invocacion explicita es `/skill`.
- Codex: usa `.agents/skills/`, `.codex/agents/`, `.codex/config.toml` y `AGENTS.md`. La invocacion explicita es `$skill`.
- Las tablas y flujos de este README describen la capacidad funcional; la sintaxis exacta depende del runtime.

## Estructura

```
.claude/                               # implementacion original para Claude Code
.agents/skills/                        # skills adaptadas para Codex
.codex/agents/                         # agentes custom para Codex
.codex/config.toml                     # configuracion de proyecto para Codex
AGENTS.md                              # reglas globales del repo para Codex
```

Cada skill es un directorio con `SKILL.md` como punto de entrada y archivos de soporte opcionales (`references/`, `scripts/`, `assets/`) que se cargan on-demand.

## Instalacion

Clonar el repo y trabajar dentro del directorio.

```bash
git clone git@github.com:jhanva/ai-skills.git
cd ai-skills
```

Para reutilizar las skills en **otro proyecto**, la copia exacta depende del runtime:

**Claude Code**

- Copiar `.claude/skills/` al proyecto, o
- agregar este repo como directorio adicional:

```bash
claude --add-dir /ruta/a/ai-skills
```

**Codex**

- Copiar `.agents/skills/`, `.codex/agents/`, `.codex/config.toml` y `AGENTS.md` a la estructura del proyecto destino
- conservar `.claude/` solo si tambien quieres mantener compatibilidad con Claude Code

Las tablas y flujos anteriores siguen siendo validos en ambos casos; lo que cambia es la capa de integracion.

## Principios

1. **No codear sin disenar** — `brainstorm` antes de todo
2. **No implementar sin test** — `tdd` siempre presente cuando cambia comportamiento
3. **No adivinar fixes** — `debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente
6. **No referenciar origenes externos** — no mencionar repos o proyectos de terceros como inspiracion en documentacion

## Ahorro de tokens

El repositorio aplica reglas base de eficiencia desde `AGENTS.md`. La skill `optimize` conserva la guia complementaria sobre delegacion y seleccion de modelo. Tecnicas de ahorro del proyecto:

| Tecnica | Tokens ahorrados por uso |
|---|---|
| Filtrar output de comando | 500-3,000 |
| Subagente para tests vs inline | 1,000-5,000 en contexto principal |
| Modelo ligero vs pesado en tarea mecanica | ~60% menos costo |
| Limpiar contexto entre tareas | todo el contexto acumulado |

Ademas:

- **Subagentes frescos por tarea** — sin contaminacion de contexto previo
- **Texto completo en prompt** — los subagentes no leen archivos del plan
- **Skills on-demand** — solo se cargan cuando se invocan o el runtime detecta relevancia
- **Archivos de referencia separados** — solo se cargan cuando la skill los necesita
- **Review de 2 etapas** — atrapa problemas temprano, evita re-trabajo costoso

## Licencia

Uso personal.
