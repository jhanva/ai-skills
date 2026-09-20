# Adaptacion del repo a Codex

Codex y Claude Code consumen la misma fuente bajo `plugins/`. La capa `.codex/` mejora la
experiencia dentro de este repo, pero ninguna skill depende de ella para funcionar.

## Estructura

```text
AGENTS.md                          # reglas concisas del proyecto
.agents/plugins/marketplace.json   # catalogo Codex
plugins/<plugin>/plugin.json       # manifest portable
plugins/<plugin>/skills/<skill>/   # SKILL.md, references, scripts y politica Codex
.codex/config.toml                 # configuracion de agentes del proyecto
.codex/agents/                     # especialistas opcionales
.codex/hooks.json                  # registro de hooks nativos
.codex/hooks/                      # handlers multiplataforma
```

## Contrato compartido

- `SKILL.md` contiene instrucciones neutrales al runtime.
- Los recursos propios se enlazan con rutas relativas a la skill.
- `agents/openai.yaml` refleja en Codex si la skill admite invocacion implicita.
- Las skills que aprovechan especialistas incluyen un fallback para el agente principal.
- La descripcion solo decide cuando cargar la skill; referencias y ejemplos se leen bajo demanda.

## Invocacion

| Claude Code | Codex |
|---|---|
| `/core:tdd` | `$tdd` |
| `disable-model-invocation: true` | `allow_implicit_invocation: false` |
| plugin instalado o `--plugin-dir` | marketplace, plugin o enlace global por skill |

Los nombres de tools no aparecen en las instrucciones compartidas. Cada runtime usa sus
capacidades disponibles para leer, buscar, editar, ejecutar y delegar.

## Marketplace y desarrollo vivo

Una instalacion de marketplace prioriza estabilidad y puede usar cache. Para desarrollar desde
este clon y ver cambios en cualquier proyecto:

```bash
python scripts/link-user-skills.py --plugin core --dry-run
python scripts/link-user-skills.py --plugin core
```

El script crea enlaces individuales en `~/.agents/skills`, conserva entradas ajenas y puede
auditarse con `--status` o revertirse con `--remove`. `--all` enlaza los cinco plugins. En Windows
la creacion de symlinks puede requerir Developer Mode o elevacion.
En ese caso, `--junction` ofrece un enlace vivo de directorio sin cambiar la politica del sistema.

## Agentes y hooks

Los agentes `task_implementer`, `reviewer`, `security_auditor`, `ui_reviewer` y `prompt_artist`
son aceleradores opcionales dentro de este proyecto. Sus prompts no asumen rutas de `plugins/`;
el caller entrega referencias resolubles cuando necesita conocimiento adicional. Los pins y su
criterio viven en [model-selection.md](model-selection.md).

Los hooks leen JSON de Codex, aplican politica local y usan comandos separados para Windows y
POSIX. El detector de UI ejecuta `plugins/design/scripts/detect.py` solo para rutas relevantes y
devuelve contexto; no bloquea la edicion.

## Verificacion

- `python -m unittest discover -s tests -v` valida manifests, portabilidad, hooks, skills y evals.
- `python scripts/link-user-skills.py --plugin core --dry-run` valida el plan de enlaces.
- Los casos en `plugins/core/evals/` cubren activacion positiva, negativa y fallback; se ejecutan
  con el evaluador del runtime cuando este disponible.
- `.github/workflows/ci.yml` repite la suite en Windows y Linux.
