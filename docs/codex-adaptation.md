# Adaptacion del repo a Codex

Esta capa replica el comportamiento del repo en Codex usando mecanismos compatibles con su documentacion oficial. Desde la conversion a marketplace de plugins, las skills se comparten con Claude Code desde `plugins/`: Codex solo aporta el catalogo, la politica de invocacion por skill, los agentes custom y los hooks.

## Base oficial

- Skills: [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- Instrucciones de proyecto con `AGENTS.md`: [developers.openai.com/codex/guides/agents-md](https://developers.openai.com/codex/guides/agents-md)
- Subagentes y agentes custom: [developers.openai.com/codex/subagents](https://developers.openai.com/codex/subagents)
- Plugins y marketplaces: [developers.openai.com/plugins/build/plugins](https://developers.openai.com/plugins/build/plugins)

## Estructura

```text
AGENTS.md                          # reglas globales oficiales del repo para Codex
.agents/plugins/marketplace.json   # catalogo de plugins en formato Codex (espejo de .claude-plugin/)
plugins/<plugin>/plugin.json       # manifest portable (Agent Plugins) que Codex lee
plugins/<plugin>/skills/<skill>/   # SKILL.md compartido + agents/openai.yaml (politica Codex)
.codex/config.toml                 # settings de subagentes del proyecto
.codex/agents/                     # agentes custom reutilizables
.codex/hooks.json                  # lifecycle hooks nativos de Codex
.codex/hooks/                      # handlers Python multiplataforma
docs/codex-adaptation.md           # esta guia
```

Detalles importantes de la organizacion nativa:

- cada skill mantiene el `SKILL.md` corto (menos de 500 lineas) y manda ejemplos, plantillas y anexos a `references/`
- el `SKILL.md` es uno solo para ambos runtimes: usa frontmatter de Claude Code y las herramientas se traducen con la tabla de `AGENTS.md`
- `${CLAUDE_PLUGIN_ROOT}` no se sustituye en Codex; equivale a la raiz del plugin (`plugins/<plugin>/`)
- los agentes custom ahora usan `.toml` cortos y cargan su conocimiento extendido desde playbooks locales dentro de `.codex/agents/<agent>/`

## Que es exclusivo de Claude Code

- `plugins/core/agents/` y `plugins/core/hooks/` (agentes y hooks de Claude Code)
- `.claude-plugin/marketplace.json` y `plugins/*/.claude-plugin/plugin.json`
- `CLAUDE.md`

## Mapeo de conceptos

| Claude Code | Codex |
|---|---|
| `plugins/<plugin>/skills/<skill>/SKILL.md` | el mismo archivo |
| `disable-model-invocation: true` | `agents/openai.yaml` con `allow_implicit_invocation: false` |
| `/skill` | `$skill` |
| `Read`, `Grep`, `Glob`, `Bash` | `rg`, `rg --files`, `find`, `sed -n`, shell puntual |
| `Agent` | `worker`, `explorer` o agentes custom en `.codex/agents/` |
| `Edit`, `Write` | herramienta nativa de patch del entorno de Codex (por ejemplo `apply_patch`) |
| `plugins/core/hooks/hooks.json` + scripts shell | `.codex/hooks.json` + handlers que leen JSON de Codex |
| skill siempre activa | reglas globales en `AGENTS.md` |

## Agentes custom agregados

Reusables por skills y por el usuario:

- `task_implementer`: backend reusable para `$execute`
- `reviewer`: backend reusable para `$review`
- `security_auditor`: backend reusable para `$secure`
- `prompt_artist`: adaptacion del agente original `prompt-artist`

Los agentes de game development viven en el repositorio hermano `gamedev-skills`.

Los pins de modelo se centralizan en `.codex/config.toml` y se propagan con
`scripts/bump-codex-model.sh <model>`.

## Comandos migrados

- La skill `git-identity` (hoy en `plugins/repo-ops/skills/git-identity/`) se expone en Codex como la skill explícita `$git-identity`. (El antiguo comando `.claude/commands/git-identity.md` se eliminó por duplicar la skill.)
- La adaptación de `$git-identity` cubre tanto hosts diferentes como mismo host con aliases SSH y auto-switch de `gh` por directorio.
- En esta adaptación, los comandos explícitos de Claude se traducen preferentemente a skills explícitas de Codex en vez de depender de una capa separada de slash-commands.

## Notas de diseño

- Las skills manuales quedaron con `allow_implicit_invocation: false`.
- Las skills automáticas (`debug`, `tdd`, `verify`) quedaron habilitadas para matching implícito.
- `optimize` se mantiene como skill de referencia, mientras que `AGENTS.md` cubre las reglas globales base del repo.
- La conversion a marketplace eliminó la copia `.agents/skills/` adaptada a Codex: la traduccion de `/skill` a `$skill` y de herramientas a `rg`/`find`/`sed -n` la aplica `AGENTS.md`, no cada `SKILL.md`.
- Los agentes custom largos se convirtieron en prompts cortos con `playbook.md`/`patterns.md` cargados on-demand, alineados con la guia oficial de skills y subagentes.
- Los hooks de Codex analizan `tool_input.command`; en `apply_patch` extraen las rutas desde el patch porque Codex no envia el campo Claude `tool_input.file_path`.
- No agregues tablas auxiliares bajo `[agents]`: Codex interpreta cada subtaba como una definicion de agente. Los pins de modelo viven en los TOML standalone de `.codex/agents/`.
