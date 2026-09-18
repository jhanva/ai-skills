<div align="center">

# ai-skills

Marketplace de plugins para desarrollo asistido por IA: skills, agentes y hooks que imponen flujos disciplinados (diseno antes de codear, TDD, debugging con causa raiz, verificacion con evidencia).

**24 skills en 5 plugins. Un catalogo, dos runtimes: Claude Code y Codex.**

[![Plugins](https://img.shields.io/badge/plugins-5-0ea5e9?style=for-the-badge)](#plugins)
[![Skills](https://img.shields.io/badge/skills-24-84cc16?style=for-the-badge)](#skills)
[![Codex Agents](https://img.shields.io/badge/codex%20agents-5-8b5cf6?style=for-the-badge)](#agentes)
[![Hooks](https://img.shields.io/badge/hooks-codex%20%2B%20claude-f97316?style=for-the-badge)](#hooks)

[Inicio rapido](#inicio-rapido) • [Plugins](#plugins) • [Instalacion](#instalacion) • [Skills](#skills) • [Flujos](#flujos-de-trabajo) • [Contribuir](#contribuir)

</div>

## Inicio rapido

Desde cualquier proyecto abierto en Claude Code:

```bash
/plugin marketplace add jhanva/ai-skills
```

```bash
/plugin install core@ai-skills
```

Listo. Ya tienes `/core:brainstorm`, `/core:plan`, `/core:tdd`, `/core:debug`, `/core:verify` y el resto del plugin `core`, mas el agente `prompt-artist` y los hooks de proteccion de `.env`. Instala `android`, `image`, `design` o `repo-ops` solo si el proyecto los necesita.

## Indice

- [Como funciona](#como-funciona)
- [Plugins](#plugins)
- [Instalacion](#instalacion)
  - [Claude Code](#claude-code)
  - [Codex](#codex)
  - [Otros agentes](#otros-agentes)
  - [Actualizar y desinstalar](#actualizar-y-desinstalar)
- [Skills](#skills)
- [Agentes](#agentes)
- [Hooks](#hooks)
- [Flujos de trabajo](#flujos-de-trabajo)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Contribuir](#contribuir)
- [Solucion de problemas](#solucion-de-problemas)
- [Repos relacionados](#repos-relacionados)
- [Principios](#principios)
- [Ahorro de tokens](#ahorro-de-tokens)

## Como funciona

El repositorio tiene tres piezas:

| Pieza | Que es | Donde vive |
|---|---|---|
| **Skill** | Un directorio con `SKILL.md` (instrucciones + frontmatter) y opcionalmente `references/`, `scripts/` y `agents/openai.yaml` | `plugins/<plugin>/skills/<skill>/` |
| **Plugin** | Un paquete instalable: un conjunto de skills, mas agentes y hooks si aplica, con un manifest que declara nombre y version | `plugins/<plugin>/` |
| **Marketplace** | El catalogo que lista los plugins y de donde obtenerlos | `.claude-plugin/marketplace.json` (Claude Code) y `.agents/plugins/marketplace.json` (Codex) |

Cada skill existe **una sola vez** y sirve a ambos runtimes:

- Claude Code lee el frontmatter de `SKILL.md` (`description`, `disable-model-invocation`, `argument-hint`, `allowed-tools`).
- Codex lee el mismo `SKILL.md` y toma la politica de invocacion de `agents/openai.yaml` (`allow_implicit_invocation`).
- Las rutas a archivos del propio plugin se escriben como `${CLAUDE_PLUGIN_ROOT}/...`. Claude Code la sustituye al cargar; en Codex equivale a `plugins/<plugin>/`.

Al instalar un plugin, sus skills quedan **namespaced** con el nombre del plugin para evitar colisiones con otros plugins: la skill `tdd` del plugin `core` se invoca como `/core:tdd`. Las skills marcadas como contextuales (`tdd`, `debug`, `verify`, `codegraph`, `optimize`) se activan solas cuando la tarea lo amerita, sin necesidad de escribir el comando.

Cada plugin declara una `version`. Solo recibes cambios cuando esa version sube en `main`, asi que una actualizacion nunca te cambia el comportamiento sin que lo pidas con `/plugin update`.

## Plugins

| Plugin | Para que | Skills | Extras |
|---|---|---|---|
| **`core`** | Cualquier proyecto. El flujo completo de desarrollo | `optimize`, `brainstorm`, `plan`, `tdd`, `debug`, `verify`, `execute`, `review`, `parallel`, `secure`, `codegraph`, `humanize` | Agentes `prompt-artist`, `reviewer`, `security-auditor`; hooks `session-context` y `block-env-access`; suite de evals |
| **`android`** | Apps Android con Clean Architecture, Room o ML on-device | `android-arch`, `bitmap-safety`, `room-audit`, `ml-ondevice` | — |
| **`image`** | Features de procesamiento de imagen (hashing, similitud, pipelines) | `image-algo`, `image-pipeline` | — |
| **`design`** | Interfaces con criterio: sistema de diseno, auditoria de UI y tokens para Jetpack Compose y web | `design-system`, `ui-review`, `ui-tokens` | Agente `ui-reviewer`; catalogo CSV (estilos, paletas con contraste validado, tipografia, guias UX con criterio WCAG, motion, reglas por stack) y buscador `search.py` sin dependencias |
| **`repo-ops`** | Operaciones de entorno y repositorio | `git-identity`, `windows-symlink`, `browser-control` | — |

Instala `core` siempre; el resto segun el proyecto. Los plugins son independientes entre si: `android` no requiere `image`, aunque `ml-ondevice` suele encadenarse con `image-pipeline`.

## Instalacion

### Claude Code

**1. Registrar el marketplace** (una vez por maquina):

```bash
/plugin marketplace add jhanva/ai-skills
```

**2. Instalar los plugins que necesites:**

```bash
/plugin install core@ai-skills
```

```bash
/plugin install android@ai-skills
```

```bash
/plugin install image@ai-skills
```

```bash
/plugin install design@ai-skills
```

```bash
/plugin install repo-ops@ai-skills
```

**3. Comprobar:** `/help` muestra las skills bajo su namespace (`core:tdd`, `android:room-audit`...). Tambien puedes abrir `/plugin` para ver el estado de cada plugin y sus errores de carga, si los hubiera.

#### Activacion automatica por proyecto

Para que un proyecto instale y active los plugins solo con abrirlo (util para equipos), anade a su `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "ai-skills": {
      "source": { "source": "github", "repo": "jhanva/ai-skills" }
    }
  },
  "enabledPlugins": {
    "core@ai-skills": true,
    "android@ai-skills": true
  }
}
```

Cuando alguien abre el proyecto y confia en la carpeta, Claude Code registra el marketplace e instala lo que aparece en `enabledPlugins`. Es la forma recomendada de fijar que plugins usa un repo.

#### Desarrollo local sin instalar

Para probar cambios en este repo o cargar los plugins desde un clon local:

```bash
claude --plugin-dir ./plugins/core --plugin-dir ./plugins/android
```

Una bandera por plugin. Tras editar una skill, `/reload-plugins` recarga sin reiniciar. Cargar la carpeta `plugins/` completa con una sola bandera requiere Claude Code 2.1.265 o superior.

Si un plugin local tiene el mismo nombre que uno instalado desde el marketplace, el local gana durante esa sesion.

### Codex

Codex lee el catalogo desde `.agents/plugins/marketplace.json` (formato nativo) y tambien reconoce `.claude-plugin/marketplace.json`. Dentro de la CLI:

```
codex
/plugins
```

Busca `ai-skills`, instala el plugin que necesites y abre una sesion nueva. Las skills se invocan con `$skill` (por ejemplo `$tdd`, `$brainstorm`).

Alternativa manual, sin marketplace: copia `plugins/<plugin>/skills/` a `.agents/skills/` del proyecto destino y lleva `.codex/` y `AGENTS.md` si quieres tambien los agentes custom y hooks nativos.

### Otros agentes

Para Cursor, Copilot, OpenCode, Cline, Windsurf y demas agentes compatibles con el formato Agent Skills:

```bash
npx skills add jhanva/ai-skills
```

El instalador detecta los directorios `skills/` de cada plugin y enlaza las skills en los agentes que tengas instalados. Solo instala skills (no agentes ni hooks). Usa `--copy` si tu sistema no permite symlinks y `-g` para instalarlas globalmente en lugar de por proyecto.

### Actualizar y desinstalar

```bash
/plugin marketplace update
```

Refresca el catalogo. Despues:

```bash
/plugin update core@ai-skills
```

Solo llega una version nueva cuando `version` sube en el `plugin.json` correspondiente.

```bash
/plugin uninstall core@ai-skills
```

```bash
/plugin marketplace remove ai-skills
```

## Skills

Los nombres de las tablas son los cortos; con el plugin instalado se invocan como `/<plugin>:<skill>` en Claude Code y `$<skill>` en Codex.

**Activacion:**

- **Contextual + explicita** — el runtime la activa solo cuando detecta la situacion (un bug, codigo nuevo, una afirmacion de exito), y ademas se puede invocar a mano.
- **Explicita** — solo se ejecuta cuando la invocas por nombre.
- **Siempre activa** — se carga como contexto base; no aparece en el menu.

### `core` — desarrollo general

| Skill | Activacion | Proposito |
|---|---|---|
| [`optimize`](./plugins/core/skills/optimize/SKILL.md) | Siempre activa | Filtrado de output de comandos, umbral para delegar a subagentes y seleccion de modelo (haiku/sonnet/opus) |
| [`brainstorm`](./plugins/core/skills/brainstorm/SKILL.md) | Explicita | Diseno antes de implementar: preguntas una a una, 2-3 enfoques con tradeoffs, spec escrita y auto-revisada |
| [`plan`](./plugins/core/skills/plan/SKILL.md) | Explicita | Convierte una spec aprobada en tareas de 2-5 minutos con codigo real, comandos y output esperado. Cero placeholders |
| [`tdd`](./plugins/core/skills/tdd/SKILL.md) | Contextual + explicita | RED-GREEN-REFACTOR estricto: prohibido codigo de produccion sin un test que falle primero |
| [`debug`](./plugins/core/skills/debug/SKILL.md) | Contextual + explicita | Debugging en 4 fases con rastreo de causa raiz; regla de los 3 intentos |
| [`verify`](./plugins/core/skills/verify/SKILL.md) | Contextual + explicita | Ninguna afirmacion de exito sin ejecutar la verificacion y leer el output |
| [`execute`](./plugins/core/skills/execute/SKILL.md) | Explicita | Ejecuta un plan tarea por tarea con subagente fresco y revision de 2 etapas (spec y calidad) |
| [`review`](./plugins/core/skills/review/SKILL.md) | Explicita | Code review con severidades (critico / importante / menor) y manejo de feedback sin sycophancy |
| [`parallel`](./plugins/core/skills/parallel/SKILL.md) | Explicita | Despacha agentes en paralelo para problemas independientes entre si |
| [`secure`](./plugins/core/skills/secure/SKILL.md) | Explicita | Analisis de seguridad: secrets, injection, auth, crypto, infra. Modo `quick` (solo diff) o `full` (proyecto). Incluye `scan-secrets.py` sin dependencias |
| [`codegraph`](./plugins/core/skills/codegraph/SKILL.md) | Contextual + explicita | Knowledge graph del proyecto: extraccion deterministica (Python via `ast`, 16 lenguajes via regex), comunidades, tags de confianza, y `query`/`path`/`explain` sin releer codigo. Zero deps, incremental, `codegraph-out/` committeable |
| [`humanize`](./plugins/core/skills/humanize/SKILL.md) | Explicita | Diagnostico (`review`) y reescritura (`rewrite`) de texto generado por IA, en espanol e ingles |

### `android`

| Skill | Activacion | Proposito |
|---|---|---|
| [`android-arch`](./plugins/android/skills/android-arch/SKILL.md) | Explicita | Valida boundaries de Clean Architecture (domain / data / presentation) |
| [`bitmap-safety`](./plugins/android/skills/bitmap-safety/SKILL.md) | Explicita | Audita pipelines de imagen: memoria, threading, manejo de errores |
| [`room-audit`](./plugins/android/skills/room-audit/SKILL.md) | Explicita | Audita seguridad de datos con Room: migraciones, schema, data safety |
| [`ml-ondevice`](./plugins/android/skills/ml-ondevice/SKILL.md) | Explicita | Integracion de modelos ML on-device: seleccion de framework y runtime |

### `image`

| Skill | Activacion | Proposito |
|---|---|---|
| [`image-algo`](./plugins/image/skills/image-algo/SKILL.md) | Explicita | Diseno de algoritmos de imagen: hashing perceptual, similitud, clustering |
| [`image-pipeline`](./plugins/image/skills/image-pipeline/SKILL.md) | Explicita | Arquitectura de pipelines multi-paso: stages, memoria, concurrencia, errores, cache |

### `design`

| Skill | Activacion | Proposito |
|---|---|---|
| [`design-system`](./plugins/design/skills/design-system/SKILL.md) | Explicita | Decide estilo, paleta, tipografia, espaciado, motion y reglas de stack consultando el catalogo; persiste `design-system/<proyecto>/MASTER.md` y overrides por pantalla. Nunca sobreescribe sin autorizacion |
| [`ui-review`](./plugins/design/skills/ui-review/SKILL.md) | Explicita | Auditoria de solo lectura de pantallas existentes: contraste medido, foco, nombres accesibles, area tactil, responsive, tokens, motion, formularios y estados. Reporte con severidades y `archivo:linea` |
| [`ui-tokens`](./plugins/design/skills/ui-tokens/SKILL.md) | Explicita | Traduce `MASTER.md` a codigo: `Theme.kt`/`Color.kt`/`Type.kt` en Compose o `tokens.css` + tema Tailwind en web, con test de contraste primero (`/tdd`) |

### `repo-ops`

| Skill | Activacion | Proposito |
|---|---|---|
| [`git-identity`](./plugins/repo-ops/skills/git-identity/SKILL.md) | Explicita | Auditoria y setup de identidades git separadas (4 capas: `includeIf`, shell guards, pre-commit, SSH). Soporta mismo host con aliases SSH |
| [`windows-symlink`](./plugins/repo-ops/skills/windows-symlink/SKILL.md) | Explicita | Audita, habilita y repara soporte de symlinks en Windows (Developer Mode, `core.symlinks`, recuperacion de checkouts) |
| [`browser-control`](./plugins/repo-ops/skills/browser-control/SKILL.md) | Explicita | Control del Chrome real del usuario via CDP: navegacion, screenshots, clicks, teclado, JS, tabs. Un WebSocket, sin frameworks; helpers Python autocontenidos |

## Agentes

| Agente | Runtime | Proposito |
|---|---|---|
| [`prompt-artist`](./plugins/core/agents/prompt-artist.md) | Claude Code (plugin `core`) | Transforma ideas en prompts narrativos para generacion de imagenes (Gemini, DALL-E, Midjourney, Stable Diffusion). Formula de 7 componentes con pesos por dominio; anexos en [`references/prompt-artist/`](./plugins/core/references/prompt-artist/) |
| [`reviewer`](./plugins/core/agents/reviewer.md) | Claude Code (plugin `core`) | Revisor de solo lectura (correccion, regresiones, tests, seguridad). `/core:review` lo despacha como `core:reviewer` |
| [`security-auditor`](./plugins/core/agents/security-auditor.md) | Claude Code (plugin `core`) | Auditor de seguridad de solo lectura por area (code, infra, deps). `/core:secure full` lo despacha en paralelo |
| [`ui-reviewer`](./plugins/design/agents/ui-reviewer.md) | Claude Code (plugin `design`) | Auditor de UI de solo lectura (accesibilidad, interaccion, layout, tokens, motion) para Compose y web. `/design:ui-review` lo despacha como `design:ui-reviewer` |
| [`prompt_artist`](./.codex/agents/prompt-artist.toml) | Codex | Equivalente de `prompt-artist` como agente custom de Codex |
| [`reviewer`](./.codex/agents/reviewer.toml) | Codex | Equivalente de `reviewer`; backend de `$review` |
| [`security_auditor`](./.codex/agents/security-auditor.toml) | Codex | Equivalente de `security-auditor`; backend de `$secure` |
| [`ui_reviewer`](./.codex/agents/ui-reviewer.toml) | Codex | Equivalente de `ui-reviewer`; backend de `$ui-review` |
| [`task_implementer`](./.codex/agents/task-implementer.toml) | Codex | Backend de `$execute`: implementa una tarea del plan con TDD. En Claude Code, `execute` despacha el subagente con prompt inline |

Los agentes de Claude Code son de solo lectura por definicion (`tools` sin `Write`/`Edit`), asi que un review o una auditoria nunca modifica el codigo.

## Hooks

Los hooks corren automaticamente en eventos del runtime. El plugin `core` los trae para Claude Code; `.codex/` los trae para Codex. Misma politica, dos implementaciones.

| Evento | Claude Code (plugin `core`) | Codex (`.codex/hooks/codex_hooks.py`) | Que hace |
|---|---|---|---|
| SessionStart | [`session-context.sh`](./plugins/core/hooks/session-context.sh) | `session-context` | Muestra branch, ultimos commits y archivos sin commit al iniciar |
| PreToolUse | [`block-env-access.sh`](./plugins/core/hooks/block-env-access.sh) | `pre-tool-policy` | Bloquea leer, escribir, redirigir, `source`, `cp`/`mv` sobre `.env*`. Permite `.env.example`, `.env.sample`, `.env.template`. En Codex ademas bloquea comandos destructivos de git |

Los hooks de Claude Code se registran en [`plugins/core/hooks/hooks.json`](./plugins/core/hooks/hooks.json) y se suman a los que el proyecto ya tenga en su `settings.json`. Los de Codex se registran en [`.codex/hooks.json`](./.codex/hooks.json) con `command` y `commandWindows` separados para no asumir un binario fijo de Python.

## Flujos de trabajo

### Desarrollo general

```
/core:brainstorm  -->  /core:plan  -->  /core:execute (aplica tdd por tarea)
                                              |
                                        /core:review  -->  /core:verify  -->  merge
```

### Debugging

```
/core:debug  -->  tdd (test que reproduce el bug)  -->  /core:verify
```

### Features de imagen

```
/image:image-algo      -->  /image:image-pipeline  -->  /core:plan  -->  /core:execute
/android:ml-ondevice   -->  /image:image-pipeline  -->  /core:plan  -->  /core:execute
```

### Interfaces (Compose o web)

```
/design:design-system  -->  /core:plan  -->  /core:execute (+ /design:ui-tokens)  -->  /design:ui-review  -->  /core:verify
   (MASTER.md)              (pantallas)       (tokens con test de contraste)          (auditoria a11y/UX)
```

`MASTER.md` vive en el proyecto consumidor (`design-system/<proyecto>/`) y es la fuente de verdad que `plan`, `execute` y `ui-tokens` leen antes de tocar UI. Consultas puntuales al catalogo: `python plugins/design/scripts/search.py "<terminos>" --domain ux` o `--stack compose`.

### Auditorias

```
/android:android-arch     boundaries de Clean Architecture
/android:bitmap-safety    memoria, threading y errores en pipelines de imagen
/android:room-audit       migraciones, schema, data safety
/core:secure quick        solo archivos cambiados (antes de commit/PR)
/core:secure full         proyecto completo (antes de release)
```

### Texto

```
/core:humanize review [archivo o texto]     diagnostico sin modificar
/core:humanize rewrite [archivo o texto]    reescritura completa
```

### Knowledge graph

```
/core:codegraph build [ruta]            construye o actualiza el grafo (incremental)
/core:codegraph query [ruta] "..."      responde desde el grafo
/core:codegraph path [ruta] "A" "B"     camino mas corto entre dos conceptos
/core:codegraph explain [ruta] "X"      un nodo y todas sus conexiones
```

### Entorno

```
/repo-ops:git-identity           auditar cuentas git
/repo-ops:git-identity setup     configurar separacion de cuentas
/repo-ops:windows-symlink        auditar symlinks en Windows (setup | repair)
/repo-ops:browser-control [tarea]
```

En Codex, sustituye `/<plugin>:` por `$`.

## Estructura del repositorio

```
.claude-plugin/marketplace.json     catalogo para Claude Code
.agents/plugins/marketplace.json    catalogo para Codex (mismos plugins, mismas versiones)
plugins/
  core/
    .claude-plugin/plugin.json      manifest para Claude Code (name, version, description)
    plugin.json                     manifest portable (estandar Agent Plugins), mismo contenido
    skills/<skill>/
      SKILL.md                      instrucciones + frontmatter
      agents/openai.yaml            politica de invocacion para Codex
      references/                   anexos que se cargan on-demand
      scripts/                      scripts de la skill (Python sin deps, PowerShell)
    agents/*.md                     agentes de Claude Code (prompt-artist, reviewer, security-auditor)
    evals/<caso>/                   suite de evals: prompt.md + graders/
    references/prompt-artist/       anexos del agente (fuera de agents/, que solo admite agentes)
    hooks/hooks.json                registro de hooks + scripts .sh
  design/
    data/*.csv, data/stacks/*.csv   catalogo UI/UX (estilos, paletas, tipografia, guias, motion, reglas por stack)
    scripts/catalog.py, search.py   indice BM25 sin dependencias, generador de MASTER.md, calculo de contraste
    agents/ui-reviewer.md           auditor de UI de solo lectura
  android/  image/  repo-ops/       misma estructura, sin agentes ni hooks
.codex/
  agents/*.toml                     agentes custom de Codex (+ playbooks en subcarpetas)
  config.toml                       settings de subagentes
  hooks.json                        registro de hooks nativos
  hooks/codex_hooks.py              handlers multiplataforma
.claude/settings.json               dogfooding: este repo instala sus propios plugins
tests/                              validacion de manifests, layout de skills, hooks y scanner
docs/codex-adaptation.md            por que la capa Codex es como es
AGENTS.md                           reglas de trabajo del repo (git, autorizaciones, convenciones)
CLAUDE.md                           catalogo y flujo para Claude Code
```

## Contribuir

Las reglas completas estan en [`AGENTS.md`](./AGENTS.md). Resumen operativo:

### Anadir una skill

1. Crear `plugins/<plugin>/skills/<nombre>/SKILL.md` con frontmatter:
   - `name` igual al directorio, `description` que diga **cuando** usarla.
   - `disable-model-invocation: true` si solo se invoca a mano; `user-invocable: false` si es siempre activa.
2. Crear `agents/openai.yaml` en la skill con `allow_implicit_invocation` coherente con el frontmatter (`false` para las de invocacion manual).
3. Mantener `SKILL.md` por debajo de 500 lineas; anexos a `references/`, scripts a `scripts/`.
4. Referenciar archivos propios como `${CLAUDE_PLUGIN_ROOT}/skills/<nombre>/...`, nunca con rutas `.claude/` o `.agents/`.
5. Subir `version` en `plugins/<plugin>/.claude-plugin/plugin.json`, `plugins/<plugin>/plugin.json` y en la entrada del plugin en **ambos** `marketplace.json`.
6. Actualizar las tablas de este README y de `CLAUDE.md`.

### Verificar antes de abrir PR

```bash
python -m unittest discover -s tests
```

```bash
claude plugin validate .
```

```bash
claude --plugin-dir ./plugins/<plugin>
```

### Evals: medir si las skills se activan

`plugins/core/evals/` contiene una suite de casos para las skills contextuales (`tdd`, `debug`, `verify`, `codegraph`) y un caso negativo que no debe activar ninguna. Cada caso es un `prompt.md` escrito como lo escribiria un usuario (sin nombrar la skill) y uno o mas `graders/*.md`: un `tool_used` que comprueba que la skill se invoco y un `llm` o `regex` sobre la respuesta.

```bash
cd plugins/core
```

```bash
claude plugin eval . --runs 3
```

Cada caso corre con el plugin y sin el; la columna `Δ` dice cuanto aporta el plugin. Un `Δ` cercano a cero con `skill-fired` fallando significa que la `description` de la skill no dispara con frases naturales: ese es el momento de reescribirla. Los resultados van a `evals/results/` (ignorado por git). Requiere una version de Claude Code que incluya `claude plugin eval`.

Los tests comprueban que los dos marketplaces listan los mismos plugins con la misma version, que cada plugin tiene sus dos manifests en sync, que `agents/` solo contiene agentes, que los hooks apuntan a scripts existentes, que cada skill tiene `openai.yaml` coherente, que ningun `SKILL.md` supera las 500 lineas ni referencia capas antiguas, que los agentes `reviewer` y `security-auditor` existen en ambos runtimes y que cada caso de eval tiene prompt y graders validos.

### Flujo git

Gitflow con `main` (publicado) y `develop` (integracion). Ramas `feature/`, `fix/`, `docs/` desde `develop`; PR con squash hacia `develop`; publicacion con merge commit `develop → main`. Commits en Conventional Commits, en espanol, sin atribucion de asistentes. Un usuario solo recibe un plugin nuevo cuando llega a `main`, porque el marketplace apunta ahi.

## Solucion de problemas

| Sintoma | Causa probable | Solucion |
|---|---|---|
| `/plugin install core@ai-skills` no encuentra el plugin | El marketplace no esta registrado o esta desactualizado | `/plugin marketplace add jhanva/ai-skills` y luego `/plugin marketplace update` |
| Instale el plugin pero no veo `/core:...` en `/help` | Los plugins se cargan al inicio de sesion | `/reload-plugins` o reiniciar Claude Code |
| Hice `git pull` y no cambio nada | La version del plugin no subio, o no actualizaste | `/plugin update core@ai-skills`; si desarrollas, usa `--plugin-dir` |
| `--plugin-dir ./plugins` carga cero plugins | Cargar una carpeta de plugins requiere 2.1.265+ | Una bandera por plugin: `--plugin-dir ./plugins/core` |
| Una skill de Codex muestra `${CLAUDE_PLUGIN_ROOT}` literal | Codex no sustituye la variable | Interpretarla como `plugins/<plugin>/` |
| Un hook de `.env` bloquea un comando legitimo | El patron cubre `.env*` salvo `.example`/`.sample`/`.template` | Renombrar el archivo a uno de los sufijos permitidos o ejecutar el comando fuera del agente |
| Tengo mi propio `prompt-artist` en `.claude/agents/` | Los agentes del proyecto tienen prioridad sobre los del plugin | Borrar la copia local para usar la del plugin |

## Repos relacionados

Las skills, agentes y hooks de **game development** (Godot 4, pixel art, Aseprite, produccion por sprints) viven en [`gamedev-skills`](https://github.com/jhanva/gamedev-skills). Se usan junto con `core` de este repo:

```bash
claude --add-dir /ruta/a/gamedev-skills
```

## Principios

1. **No codear sin disenar** — `brainstorm` antes de todo
2. **No implementar sin test** — `tdd` siempre presente cuando cambia comportamiento
3. **No adivinar fixes** — `debug` con causa raiz primero
4. **No decir "listo" sin evidencia** — `verify` antes de reportar
5. **No confiar en reportes de subagentes** — verificar independientemente
6. **No referenciar origenes externos** — el contenido se presenta como propio

## Ahorro de tokens

La skill `optimize` (siempre activa en `core`) y las reglas de `AGENTS.md` aplican estas tecnicas en toda interaccion:

| Tecnica | Tokens ahorrados por uso |
|---|---|
| Filtrar output de comando con pipes | 500-3,000 |
| Subagente para tests vs inline | 1,000-5,000 en contexto principal |
| Modelo ligero vs pesado en tarea mecanica | ~60% menos costo |
| Limpiar contexto entre tareas | todo el contexto acumulado |

Ademas: subagentes frescos por tarea, texto completo de la tarea en el prompt (el subagente no lee el plan), skills y `references/` cargados solo cuando hacen falta, y review de 2 etapas para evitar re-trabajo.

## Licencia

Uso personal.
