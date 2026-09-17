# Reglas de trabajo — ai-skills

Estas reglas aplican a todo el repositorio y a cualquier agente o persona que trabaje en el,
tanto desde Claude Code como desde Codex.

## Alcance y principios

- Trabajar en espanol. El texto del repositorio se escribe sin tildes ni enes, siguiendo la
  convencion existente en skills, agentes y documentacion.
- Este repositorio contiene **skills, agentes y hooks** reutilizables para desarrollo asistido
  por IA. No contiene aplicaciones ni proyectos finales: esos viven en otros repos y consumen lo
  que aqui se define.
- El dominio de game development (Godot 4, pixel art, produccion de juegos) vive en el
  repositorio hermano `gamedev-skills`. No anadir aqui skills, agentes ni hooks de ese dominio;
  ambos repos se usan juntos en un proyecto de juego.
- El repo es un marketplace de plugins con una sola copia de cada skill:
  - `plugins/<plugin>/skills/<skill>/` contiene el `SKILL.md` (frontmatter de Claude Code) y
    `agents/openai.yaml` (politica de invocacion de Codex). Ambos runtimes leen el mismo directorio.
  - `.claude-plugin/marketplace.json` (Claude Code) y `.agents/plugins/marketplace.json` (Codex)
    listan los mismos plugins con la misma `version` que su `plugin.json`.
  - `.codex/agents/`, `.codex/config.toml`, `.codex/hooks.json` y `.codex/hooks/` son la capa
    nativa de Codex para agentes y hooks; `plugins/core/agents/` y `plugins/core/hooks/` son la de
    Claude Code. Un cambio de comportamiento en un agente o hook se replica en ambas dentro del
    mismo PR, salvo que el usuario pida lo contrario de forma explicita.
- El contenido se presenta como propio. No mencionar repos, librerias ni proyectos de terceros
  como origen o inspiracion en skills, agentes ni documentacion.
- No inventar identificadores de modelos, tools de MCP ni campos de configuracion. Si no se puede
  comprobar que existe, se senala; no se rellena con suposiciones presentadas como hechos.
- Preferir cambios pequenos, trazables y limitados a lo pedido. Entregar lo solicitado y
  detenerse ahi; si hacen falta pasos adicionales, exponerlos y esperar la decision.

## Autorizacion

El agente tiene autonomia sobre el flujo de git completo dentro de las reglas de la seccion
[Git](#git). Se puede hacer sin pedir permiso:

- Leer cualquier archivo del repositorio.
- Crear y editar archivos del repositorio.
- Correr la suite de pruebas (`python -m unittest discover -s tests`).
- Ejecutar hooks y scripts del repo en modo local para verificarlos.
- Crear ramas de trabajo, hacer `git commit` y `git push` sobre ellas.
- Abrir *pull requests* hacia `develop` (o hacia `main` desde `hotfix/` o desde `develop`).
- **Integrar los *pull requests*** que cumplan la lista de verificacion de la seccion
  [Pull requests](#pull-requests), con el modo de integracion que corresponda.
- Borrar la rama de trabajo una vez que su contenido esta en `develop`.

Requiere permiso explicito, individual y para esa sola vez:

- Escribir directamente sobre `main` o `develop` sin pasar por un PR.
- `git push --force`, `git rebase` sobre ramas ya publicadas, `git reset --hard` y cualquier
  operacion que reescriba historial compartido.
- Borrar o renombrar `main` o `develop`. **`develop` no se elimina nunca.**
- Cambiar la configuracion del repositorio en GitHub (proteccion de ramas, modos de merge,
  rama por defecto).
- Cambiar los pins de modelo en `.codex/agents/*.toml` (via `scripts/bump-codex-model.sh`).
- Anadir o cambiar dependencias, servidores MCP o claves/credenciales de cualquier tipo.
- Borrar o renombrar una skill, agente o hook existente.
- Cualquier accion sobre servicios externos (GitHub u otros).

Antes de pedir permiso, explicar que se hara, sobre que archivos o sistemas y que consecuencias
tiene. Una autorizacion no se extiende a acciones posteriores, similares ni derivadas.

## Git

El repositorio sigue gitflow con dos ramas permanentes y ramas de trabajo desechables.

### Ramas permanentes

- `main`: lo publicado y utilizable desde otros proyectos. Cada commit en `main` es un estado
  estable del stack de skills. Solo se actualiza por *pull request* desde `develop` o desde una
  rama `hotfix/`.
- `develop`: lo integrado y pendiente de publicar. Solo se actualiza por *pull request* desde
  ramas de trabajo.
- Ninguna de las dos se elimina, renombra ni recibe `push --force`. No escribir nunca
  directamente sobre ellas.

### Ramas de trabajo

- Todo cambio nace en una rama creada desde `develop` **actualizada**: antes de ramificar,
  `git fetch --prune` y `git pull --ff-only` sobre `develop`.
- Prefijo `feature/` para trabajo nuevo, mejoras y refactors planificados; `fix/` para
  correcciones que no son urgentes; `hotfix/` para correcciones urgentes sobre lo publicado
  (nace de `main` y se integra en `main` y despues en `develop`). Las ramas creadas por agentes
  pueden usar `agent/` para distinguirlas; siguen las mismas reglas que `feature/`.
- Nombre en minusculas, palabras separadas por guion, sin tildes ni espacios:
  `feature/skill-humanize`, `fix/codex-hooks-windows`, `hotfix/secret-scanner-falso-positivo`.
- Una rama por asunto. No mezclar cambios sin relacion.
- Una rama `feature/`, `fix/`, `agent/` o `hotfix/` se borra **solo cuando su contenido ya esta
  en `develop`**. Para `hotfix/` eso ocurre despues del PR `main → develop`, no al entrar en
  `main`. Como se integra con *squash*, `git branch -d` la reporta como no integrada: comprobar
  con `git diff origin/develop` que el contenido ya esta alli antes de forzar el borrado.
- El borrado no es una regla global del repositorio: se decide **en cada PR** al integrarlo
  (`--delete-branch` en `gh`, o la casilla equivalente en GitHub). Se marca solo en los PR cuyo
  destino es `develop`.

### Integracion

| Origen → destino | Modo | Borrar rama origen | Motivo |
|---|---|---|---|
| `feature/`, `fix/`, `agent/` → `develop` | **Squash** | Si | La rama es desechable; sus commits intermedios no aportan al historial |
| `hotfix/` → `main` | **Squash** | No | Igual que arriba, pero la rama aun tiene que llegar a `develop` |
| `main` → `develop` (tras un hotfix) | **Merge commit** | No aplica; despues se borra `hotfix/` a mano | Lleva la correccion publicada a la linea de integracion |
| `develop` → `main` | **Merge commit** | **Nunca** | Sin squash: conserva `develop` como antepasado de `main` y marca el punto exacto de cada publicacion |

`main` y `develop` conviven de forma permanente. Si `develop → main` se hiciera con *squash* o
*rebase*, `main` tendria el mismo contenido con commits distintos, `develop` dejaria de ser su
antepasado y cada publicacion posterior arrastraria conflictos sobre cambios ya integrados. El
*merge commit* evita eso y deja auditable que se publico y cuando.

Con `gh`:

```bash
gh pr merge <numero> --squash --delete-branch   # feature/, fix/, agent/ -> develop
gh pr merge <numero> --squash                   # hotfix/ -> main (la rama se conserva)
gh pr merge <numero> --merge                    # main -> develop tras un hotfix
git push origin --delete hotfix/<nombre>        # solo cuando el hotfix ya esta en develop
gh pr merge <numero> --merge                    # develop -> main: sin --squash, sin --delete-branch
```

### Commits

Los mensajes siguen [Conventional Commits 1.0.0](https://www.conventionalcommits.org/es/v1.0.0/),
en espanol:

```
<tipo>(<alcance>): <descripcion>

[cuerpo opcional: el porque, no el que]

[pie opcional]
```

- Tipo, alcance y descripcion en minuscula; descripcion en imperativo, sin punto final, maximo
  72 caracteres en la primera linea.
- El cuerpo explica el porque. El que ya esta en el diff.

| Tipo | Cuando se usa |
|---|---|
| `feat` | Skill, agente o hook nuevo, o capacidad nueva en uno existente |
| `fix` | Correccion de un comportamiento equivocado |
| `refactor` | Reorganiza contenido sin cambiar comportamiento (slim, extraer `references/`) |
| `perf` | Reduce tokens o tiempo sin cambiar comportamiento |
| `test` | Anade o corrige pruebas en `tests/` |
| `docs` | Solo documentacion (README, `docs/`, `CLAUDE.md`, `AGENTS.md`) |
| `build` | Dependencias, scripts de build, pins de modelo |
| `ci` | Configuracion de integracion continua |
| `chore` | Mantenimiento: `.gitignore`, `.gitattributes`, settings, limpieza |
| `revert` | Revierte un commit anterior |

Alcances admitidos: el nombre de la skill o agente afectado (`secure`, `tdd`, `browser-control`,
`prompt-artist`), o una capa del repo: `claude`, `codex`, `hooks`, `docs`, `repo`, `tests`. Si el cambio cruza varias skills, se omite el alcance.

Un cambio incompatible — cambiar el protocolo de un subagente, renombrar una skill, cambiar el
formato que consumen los hooks — se marca con `!` tras el alcance y se explica en el pie con
`BREAKING CHANGE:`.

Ejemplos:

```
feat(secure): agregar patrones de seguridad para docker

fix(codex): extraer rutas del patch en hooks de apply_patch

refactor(debug): simplificar el flujo de rastreo de causa raiz

docs: actualizar README con el uso de /secure

feat(execute)!: cambiar el protocolo de despacho de subagentes

BREAKING CHANGE: los subagentes reciben el texto de la tarea directamente
en lugar de rutas de archivo.
```

**Sin atribucion de asistentes.** Los commits y PR se atribuyen unicamente a las personas del
equipo: no se anaden trailers `Co-Authored-By` de asistentes, herramientas o modelos, ni lineas
del tipo "Generated with".

### Pull requests

- El flujo existe por orden, no por revision de terceros. El agente abre e integra los PR por su
  cuenta; que nada entre directo a `main` o `develop` es disciplina, no una barrera tecnica.
- El titulo sigue la convencion de commits. Con *squash*, el titulo del PR se convierte en el
  mensaje del commit integrado.
- La descripcion indica que cambia, por que, archivos afectados, como se probo y que capa
  (Claude, Codex o ambas) se toco.
- Un PR por asunto. Si toca frentes sin relacion, se separa.

Lista de verificacion antes de integrar. Si algun punto falla, el PR se queda abierto y se
informa al usuario en lugar de mergear:

1. La rama esta actualizada con su destino (`develop` o `main`) y no tiene conflictos.
2. `python -m unittest discover -s tests` pasa.
3. `.claude/settings.local.json`, `__pycache__/`, `tmp/` y cualquier archivo con credenciales
   no aparecen en la lista de cambios.
4. Si se anadio, renombro o elimino una skill, agente o hook, la documentacion esta
   actualizada segun la seccion [Documentacion](#documentacion).
5. Se usa el modo de integracion de la tabla de la seccion [Integracion](#integracion).

Un PR `develop → main` (publicacion) se abre solo cuando el usuario lo pide o cuando el trabajo
acordado para esa entrega esta completo e integrado en `develop`.

## Skills, agentes y hooks

El porque de la adaptacion a Codex esta en [docs/codex-adaptation.md](docs/codex-adaptation.md);
el catalogo de skills y su modo de invocacion en [CLAUDE.md](CLAUDE.md) y el README. Reglas que
no se negocian al tocar cualquiera de las tres capas:

- Cada skill es un directorio con `SKILL.md` como punto de entrada y frontmatter valido.
  `SKILL.md` se mantiene por debajo de 500 lineas; ejemplos, plantillas y anexos van a
  `references/`, scripts a `scripts/`. Las rutas a archivos propios del plugin se escriben con
  `${CLAUDE_PLUGIN_ROOT}/...`, nunca con `.claude/` ni `.agents/`.
- Una skill pertenece a un solo plugin (`core`, `android`, `image`, `repo-ops`). Anadir, mover o
  renombrar una skill implica actualizar los dos `marketplace.json`, subir `version` en el
  `plugin.json` afectado (ambos manifests) y pasar `claude plugin validate .`.
- `plugins/*/agents/` solo contiene definiciones de agente (`.md` con frontmatter); Claude Code
  carga todo lo que hay ahi. Los anexos de un agente van a `plugins/*/references/`.
- Modo de invocacion explicito en el frontmatter: `user-invocable: false` para skills siempre
  activas, `disable-model-invocation: true` para las que solo invoca el usuario. En Codex el
  equivalente es `agents/openai.yaml` con `allow_implicit_invocation`.
- Los agentes de Codex (`.codex/agents/*.toml`) llevan `name`, `description`,
  `developer_instructions` y un pin de modelo real. El conocimiento extendido va en su playbook
  local dentro de `.codex/agents/<agent>/`.
- Todo cambio en `.codex/hooks/codex_hooks.py`, en la configuracion de agentes o en los manifests
  de plugins lleva prueba en `tests/`.
- Los hooks deben funcionar en Windows, macOS y Linux. No asumir un binario fijo de Python:
  `.codex/hooks.json` define `command` y `commandWindows` por separado.
- Antes de un commit: `python -m unittest discover -s tests`. No declarar exito sin leer el
  output.

### Reglas especificas para Codex

- La invocacion explicita de skills es con `$skill`, no con `/skill`. Codex no sustituye
  `${CLAUDE_PLUGIN_ROOT}`: se resuelve como la raiz del plugin (`plugins/<plugin>/`).
- Si una instruccion heredada de `.claude/` menciona herramientas de Claude, se traduce asi:
  - `Read` / `Grep` / `Glob` / `Bash` → `rg`, `rg --files`, `find`, `sed -n`, shell puntual
  - `Agent` → agentes built-in (`worker`, `explorer`) o agentes custom en `.codex/agents/`
  - `Edit` / `Write` → la herramienta nativa de patch del entorno (por ejemplo `apply_patch`)
  - `WebFetch` / `WebSearch` → browsing web segun la politica del entorno
- Hacer lecturas minimas y puntuales antes de abrir archivos completos.
- Usar `multi_tool_use.parallel` cuando varias lecturas o inspecciones sean independientes.
- Filtrar output ruidoso de comandos antes de traerlo a contexto.

## Documentacion

- Un PR que anade, renombra o elimina una skill, agente o hook actualiza en el mismo PR:
  la tabla y el arbol de `CLAUDE.md`, las tablas del README (incluidos los contadores del
  encabezado) y, si toca la capa Codex, `docs/codex-adaptation.md`.
- La documentacion explica el **porque**; `SKILL.md`, los `.toml` y los hooks son la fuente de
  verdad del que.
- Los enlaces internos usan rutas relativas al repo y deben resolver a archivos existentes.

## Archivos y salidas

- No crear carpetas `output/`, `tmp/`, `temp/` ni similares dentro del repositorio. Los
  temporales van fuera del proyecto.
- No versionar `.claude/settings.local.json`, `__pycache__/`, archivos de entorno ni
  credenciales de MCP. Comprobar `git status` antes de cada commit.
- No crear copias con sufijos `copia`, `nuevo`, `final`, `v2`. Un archivo vigente por asunto.
- Leer y escribir texto como UTF-8 sin BOM. Finales de linea segun `.gitattributes`: LF por
  defecto y en `.sh`, CRLF en `.ps1`.

## Cierre de cada tarea

- Indicar que archivos se crearon o modificaron y en que capa (Claude, Codex o ambas).
- Indicar que se verifico (pruebas, ejecucion de hooks, revision manual) y que no fue posible
  verificar.
- Si quedo algo pendiente o fuera de alcance, decirlo de forma explicita.
