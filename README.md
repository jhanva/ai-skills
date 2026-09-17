<div align="center">

# ai-skills

Convierte un repositorio en un stack de desarrollo asistido por IA con skills, agentes y reglas reutilizables.

**21 skills. 4 agentes de Codex. Hooks nativos en Codex y Claude. Dos runtimes, un mismo workflow.**

[![Skills](https://img.shields.io/badge/skills-21-84cc16?style=for-the-badge)](#skills)
[![Codex Agents](https://img.shields.io/badge/codex%20agents-4-8b5cf6?style=for-the-badge)](#agentes)
[![Hooks](https://img.shields.io/badge/hooks-codex%20%2B%20claude-f97316?style=for-the-badge)](#hooks)
[![Runtimes](https://img.shields.io/badge/runtimes-2-0ea5e9?style=for-the-badge)](#compatibilidad-por-runtime)

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
- [Browser Automation](#browser-automation)
- [Knowledge Graph](#knowledge-graph)
- [Agentes](#agentes)
- [Flujos de trabajo](#flujos-de-trabajo)
- [Compatibilidad por runtime](#compatibilidad-por-runtime)
- [Instalacion](#instalacion)
- [Estructura](#estructura)
- [Repos relacionados](#repos-relacionados)

## Que incluye

| Categoria | Cantidad | Descripcion |
|---|---:|---|
| Skills | 21 | Workflows para desarrollo general, Android, imagen, browser automation, knowledge graphs, texto y operaciones de repo |
| Agentes Codex | 4 | Implementacion, review, seguridad y prompt design |
| Hooks Codex | 2 handlers | Politica pre-tool y contexto de sesion |
| Hooks Claude | 2 | Implementacion original equivalente para Claude Code |
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

### Browser automation

| Skill | Activacion | Proposito |
|---|---|---|
| [`browser-control`](./.agents/skills/browser-control/SKILL.md) | Explicita | Control directo del browser via CDP (Chrome DevTools Protocol). Conecta al Chrome real del usuario y ejecuta navegacion, screenshots, clicks por coordenadas, input de teclado, evaluacion JS y manejo de tabs. Sin frameworks intermedios — un WebSocket al browser, scripts Python inline con libreria de helpers autocontenida |

Incluye libreria Python CDP (`cdp_helpers.py`, ~370 lineas) con auto-discovery de Chrome, guia de conexion (Way 1: checkbox en chrome://inspect, Way 2: flag de linea de comandos) y referencia de patrones para mecanicas web complejas (dialogs, iframes, shadow DOM, uploads, dropdowns).

### Knowledge graph

| Skill | Activacion | Proposito |
|---|---|---|
| [`codegraph`](./.agents/skills/codegraph/SKILL.md) ([Claude Code](./.claude/skills/codegraph/SKILL.md)) | Contextual + explicita | Convierte cualquier proyecto (codigo, SQL, docs, configs) en un knowledge graph persistente y consultable. Extraccion deterministica (Python via ast nativo, 16 lenguajes via regex), clustering de comunidades por modularidad, tags de confianza EXTRACTED/INFERRED/AMBIGUOUS, y comandos query/path/explain que responden desde el grafo sin releer el codigo |

Disponible en ambos runtimes: `$codegraph` en Codex y `/codegraph` en Claude Code. Zero dependencias (solo stdlib de Python 3.10+, sin pip install), pipeline completo en un comando, builds incrementales por hash de contenido. Outputs: `graph.json` (node-link, compatible d3/GraphRAG), `GRAPH_REPORT.md` (god nodes, conexiones sorprendentes, preguntas sugeridas) y `graph.html` (visualizacion interactiva offline). El directorio `codegraph-out/` es committeable: el equipo comparte un solo grafo.

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

## Hooks

Codex carga [`hooks.json`](./.codex/hooks.json) desde la capa confiable del
proyecto. Los handlers multiplataforma viven en
[`codex_hooks.py`](./.codex/hooks/codex_hooks.py) y consumen el JSON nativo de
`PreToolUse` y `SessionStart`.

| Handler Codex | Evento | Que valida |
|---|---|---|
| `pre-tool-policy` | PreToolUse (Bash/apply_patch) | Bloquea `.env`, comandos destructivos y edits protegidos |
| `session-context` | SessionStart | Branch, commits y archivos modificados |

La capa Claude tiene los scripts equivalentes. Comparten biblioteca `_parse.sh` para parsing JSON.

| Hook | Evento | Que valida |
|---|---|---|
| [`block-env-access.sh`](./.claude/hooks/block-env-access.sh) | PreToolUse (Bash) | Bloquea lectura/escritura/source de archivos `.env` (permite `.env.example`, `.env.sample`, `.env.template`) |
| [`session-context.sh`](./.claude/hooks/session-context.sh) | SessionStart | Muestra branch, commits recientes y archivos modificados sin commit |

## Comandos

| Comando | Proposito |
|---|---|
| [`git-identity`](./.agents/skills/git-identity/SKILL.md) | Auditoria de cuentas git (4 capas: includeIf, shell guards, pre-commit hook, SSH keys) |
| [`git-identity setup`](./.agents/skills/git-identity/SKILL.md) | Configurar separacion de cuentas (macOS/Linux/Windows, mismo host o hosts diferentes) |

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

### Browser automation

```
browser-control [tarea]     (conecta al browser y ejecuta la tarea)
```

### Knowledge graph

```
codegraph build [ruta]           (construye/actualiza el grafo, incremental)
codegraph query [ruta] "..."     (responde desde el grafo, BFS o --dfs)
codegraph path [ruta] "A" "B"    (camino mas corto entre dos conceptos)
codegraph explain [ruta] "X"     (un nodo y todas sus conexiones)
```

### Multiples problemas independientes

```
parallel  -->  verify
```

## Compatibilidad por runtime

- Claude Code: usa `.claude/skills/`, `.claude/agents/`, `.claude/commands/` y hooks. La invocacion explicita es `/skill`.
- Codex: usa `.agents/skills/`, `.codex/agents/`, `.codex/config.toml`, `.codex/hooks.json` y `AGENTS.md`. La invocacion explicita es `$skill`.
- Las tablas y flujos de este README describen la capacidad funcional; la sintaxis exacta depende del runtime.

## Estructura

```
.claude/                               # implementacion original para Claude Code
.agents/skills/                        # skills adaptadas para Codex
.codex/agents/                         # agentes custom para Codex
.codex/config.toml                     # configuracion de proyecto para Codex
.codex/hooks.json                      # registro de hooks nativos de Codex
.codex/hooks/codex_hooks.py            # handlers Python multiplataforma
AGENTS.md                              # reglas globales del repo para Codex
```

Cada skill es un directorio con `SKILL.md` como punto de entrada y archivos de soporte opcionales (`references/`, `scripts/`, `assets/`) que se cargan on-demand.

## Repos relacionados

Las skills, agentes, hooks y plugins de **game development** (Godot 4, pixel art, Aseprite, PixelLab, produccion por sprints) se movieron a [`gamedev-skills`](https://github.com/jhanva/gamedev-skills). Si usabas `/game-concept`, `/rpg-design`, `/godot-setup`, `/sprite-spec`, `/sprint`, la jerarquia de agentes de estudio o los plugins MCP desde este repo, clona el nuevo y carga ambos:

```bash
claude --add-dir /ruta/a/ai-skills --add-dir /ruta/a/gamedev-skills
```

Los flujos de juego siguen usando `/brainstorm`, `/plan`, `/tdd`, `/execute`, `/review` y `/verify` de este repo.

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

- Copiar `.agents/skills/`, `.codex/agents/`, `.codex/config.toml`, `.codex/hooks.json`, `.codex/hooks/` y `AGENTS.md` a la estructura del proyecto destino
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
