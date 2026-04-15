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

## Que se mantuvo intacto

- `.claude/skills/`
- `.claude/agents/`
- `CLAUDE.md`
- `README.md`

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

- `task_implementer`: backend reusable para `$execute`
- `reviewer`: backend reusable para `$review`
- `security_auditor`: backend reusable para `$secure`
- `prompt_artist`: adaptacion del agente original `prompt-artist`

## Notas de diseño

- Las skills manuales quedaron con `allow_implicit_invocation: false`.
- Las skills automáticas (`debug`, `tdd`, `verify`) quedaron habilitadas para matching implícito.
- `optimize` se duplicó como skill de referencia, pero sus reglas base se movieron al `AGENTS.md` oficial del repo para evitar depender de archivos no documentados.
