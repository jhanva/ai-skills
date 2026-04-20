# Adaptacion del repo a Codex

Esta capa nueva replica el comportamiento del repo original usando mecanismos compatibles con la documentacion oficial de Codex.

## Base oficial

- Skills: [developers.openai.com/codex/skills](https://developers.openai.com/codex/skills)
- Instrucciones de proyecto con `AGENTS.md`: [developers.openai.com/codex/guides/agents-md](https://developers.openai.com/codex/guides/agents-md)
- Subagentes y agentes custom: [developers.openai.com/codex/subagents](https://developers.openai.com/codex/subagents)

## Estructura nueva

```text
AGENTS.md                   # reglas globales oficiales del repo para Codex
.agents/skills/             # skills nativas para Codex
.codex/config.toml          # settings de subagentes del proyecto
.codex/agents/              # agentes custom reutilizables
docs/codex-adaptation.md    # esta guia
```

Detalles importantes de la organizacion nativa:

- cada skill de Codex mantiene el `SKILL.md` corto y manda ejemplos, plantillas y anexos a `references/`
- las skills quedaron por debajo de 500 lineas siguiendo el patron de progressive disclosure de Codex
- los agentes custom ahora usan `.toml` cortos y cargan su conocimiento extendido desde playbooks locales dentro de `.codex/agents/<agent>/`

## Que se mantuvo intacto

- `.claude/skills/`
- `.claude/agents/`
- `CLAUDE.md`

## Mapeo de conceptos

| Claude Code | Codex |
|---|---|
| `.claude/skills/<skill>/SKILL.md` | `.agents/skills/<skill>/SKILL.md` |
| `disable-model-invocation: true` | `agents/openai.yaml` con `allow_implicit_invocation: false` |
| `/skill` | `$skill` |
| `Read`, `Grep`, `Glob`, `Bash` | `rg`, `rg --files`, `find`, `sed -n`, shell puntual |
| `Agent` | `worker`, `explorer` o agentes custom en `.codex/agents/` |
| `Edit`, `Write` | herramienta nativa de patch del entorno de Codex (por ejemplo `apply_patch`) |
| skill siempre activa | reglas globales en `AGENTS.md` |

## Agentes custom agregados

Reusables por skills y por el usuario:

- `task_implementer`: backend reusable para `$execute`
- `reviewer`: backend reusable para `$review`
- `security_auditor`: backend reusable para `$secure`
- `prompt_artist`: adaptacion del agente original `prompt-artist`

Jerarquia gamedev (mirror directo de `.claude/agents/gamedev/`):

- Directores: `creative_director`, `technical_director`
- Especialistas: `game_designer`, `level_designer`, `godot_architect`,
  `pixel_artist`, `sound_designer`, `qa_analyst`, `producer`

Los pins de modelo se centralizan en `.codex/config.toml` y se propagan con
`scripts/bump-codex-model.sh <model>`.

## Comandos migrados

- El comando de Claude `.claude/commands/git-identity.md` se integró en Codex como la skill explícita `$git-identity` dentro de `.agents/skills/git-identity/`.
- La adaptación de `$git-identity` cubre tanto hosts diferentes como mismo host con aliases SSH y auto-switch de `gh` por directorio.
- En esta adaptación, los comandos explícitos de Claude se traducen preferentemente a skills explícitas de Codex en vez de depender de una capa separada de slash-commands.

## Notas de diseño

- Las skills manuales quedaron con `allow_implicit_invocation: false`.
- Las skills automáticas (`debug`, `tdd`, `verify`) quedaron habilitadas para matching implícito.
- `optimize` se mantiene como skill de referencia, mientras que `AGENTS.md` cubre las reglas globales base del repo.
- En la pasada de ajuste para Codex se normalizaron las invocaciones explicitas a `$skill` y los ejemplos operativos a herramientas nativas como `rg`, `find` y `sed -n`.
- La pasada final de optimizacion dejó todas las `SKILL.md` bajo 500 lineas y convirtió los agentes custom largos en prompts cortos con `playbook.md`/`patterns.md` cargados on-demand, alineados con la guia oficial de skills y subagentes.
