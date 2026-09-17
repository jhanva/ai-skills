# Plan — Separar game dev en su propio repositorio

Estado: ejecutado el 2026-09-17. Fase 1 en jhanva/gamedev-skills, Fase 2 en este repo. Se ejecuta en dos repositorios con el flujo de `AGENTS.md`
(rama `feature/` desde `develop`, squash a `develop`, merge commit a `main`).

## Decisiones tomadas (cambiar aqui antes de ejecutar)

| Decision | Valor |
|---|---|
| Nombre del repo nuevo | `gamedev-skills` |
| Ruta local | `C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios/gamedev-skills` |
| Remoto | `https://github.com/jhanva/gamedev-skills.git` (publico, como `ai-skills`) |
| Historial | No se migra. El repo nuevo nace con un commit inicial; el historial queda en `ai-skills` |
| Dependencia entre repos | Ninguna en runtime. Cada repo se instala solo. Un proyecto de juego usa ambos (`claude --add-dir` x2 o copia de ambas capas) |
| Infra compartida (`_parse.sh`, `codex_hooks.py` base, `AGENTS.md`) | Se **copia**, no se enlaza. Dos repos independientes es mas simple que uno que requiere al otro |
| `pets/` | Va a `gamedev-skills`. Son pixel art regenerado con PixelLab; no tienen relacion con skills core |
| `prompt-artist` | Se queda en `ai-skills`. Genera prompts de imagen para cualquier dominio |

## Criterio de corte

Se mueve todo lo que solo tiene sentido con Godot, GDD, pixel art o produccion de juegos.
`sprint`, `story`, `scope-check`, `playtest` y `smoke-test` se mueven aunque suenen genericos:
leen `design/gdd/`, `production/sprints/` y velocity de stories de juego.

## Mapa de archivos

### Se mueven a `gamedev-skills` (y se borran de `ai-skills`)

```
.claude/skills/            (23)  rpg-design game-arch pixel-pipeline game-start game-concept
                                 art-bible design-system level-brief balance-check sprite-spec
                                 tileset-spec palette sound-brief godot-setup scene-design
                                 sprint story scope-check playtest smoke-test
                                 aseprite-workflows godot-workflows pixellab-workflows
.agents/skills/            (20)  los mismos menos aseprite/godot/pixellab-workflows
                                 (en Codex viven dentro de plugins/)
.claude/agents/gamedev/     (9)  creative-director technical-director game-designer
                                 level-designer godot-architect pixel-artist sound-designer
                                 qa-analyst producer
.codex/agents/              (9 .toml + 9 dirs de playbook) los mismos nombres
.claude/hooks/              (3)  validate-gameplay-code.sh validate-assets.sh
                                 check-design-coverage.sh
plugins/                   (3)  aseprite-codex godot-codex pixellab-codex
pets/                            README.md albedo/ the-lich-king/
.agents/plugins/marketplace.json
.mcp.json                        (aseprite, godot, pixellab: los 3 servers son gamedev)
```

### Se copian a `gamedev-skills` (y se quedan tambien en `ai-skills`)

```
.claude/hooks/_parse.sh
.claude/hooks/block-env-access.sh
.claude/hooks/session-context.sh          (gamedev conserva la version con sprint activo)
.codex/hooks/codex_hooks.py               (gamedev conserva pre-tool-policy + todo lo gamedev)
.codex/hooks.json
.codex/config.toml
.claude/settings.json
.gitattributes  .gitignore
AGENTS.md                                 (adaptado: alcance y ejemplos de gamedev)
scripts/bump-codex-model.sh               (cada repo con su lista de agentes)
```

### Se modifican en `ai-skills`

```
.claude/hooks/session-context.sh          quitar "Game Dev Session" y sprint activo
.codex/hooks/codex_hooks.py               quitar validate_gameplay_code, post_edit_checks,
                                          regexes gamedev; session_context neutro
.codex/hooks.json                         quitar los 2 hooks gamedev
.claude/settings.json                     quitar los 3 hooks gamedev
tests/test_codex_adaptation.py            quitar 5 tests gamedev (van al repo nuevo)
scripts/bump-codex-model.sh               dejar solo 4 agentes core
README.md  CLAUDE.md  AGENTS.md  docs/codex-adaptation.md   quitar secciones gamedev, contadores
```

### Se quedan en `ai-skills` sin tocar

```
.claude/skills/ (21)  optimize brainstorm plan tdd debug verify execute review parallel secure
                      android-arch bitmap-safety room-audit image-algo ml-ondevice image-pipeline
                      humanize windows-symlink browser-control git-identity codegraph
.agents/skills/ (21)  los mismos
.claude/agents/       prompt-artist.md + prompt-artist/
.codex/agents/        prompt-artist.toml + prompt-artist/  reviewer.toml  security-auditor.toml
                      task-implementer.toml
.claude/hooks/        _parse.sh block-env-access.sh session-context.sh
```

## Reparto de tests

| Test actual | Destino |
|---|---|
| `test_project_config_contains_only_real_agent_settings` | ambos |
| `test_custom_agents_have_required_codex_fields` | ambos |
| `test_gamedev_agents_do_not_implicitly_run_user_skills` | gamedev |
| `test_hooks_are_registered_with_cross_platform_commands` | ambos |
| `test_model_bump_helper_only_updates_standalone_agent_files` | ambos |
| `test_pre_tool_policy_blocks_env_but_allows_template` | ambos |
| `test_pre_tool_policy_blocks_destructive_git_command` | ambos |
| `test_post_edit_checks_understand_apply_patch_paths` | gamedev |
| `test_post_edit_checks_warn_when_gameplay_has_no_gdd` | gamedev |
| `test_secure_scanner_is_native_and_has_fixed_classification` | core |
| `test_secure_scanner_detects_a_token_and_help_is_successful` | core |
| `test_godot_fixes_are_present_in_codex_skills` | gamedev |
| `test_planning_fixes_are_consistent` | gamedev |
| `test_readme_points_to_native_browser_skill_and_codex_hooks` | core |
| `test_browser_helpers_include_cross_platform_fixes` | core |

Resultado esperado: core 10 tests, gamedev 11 tests (6 comunes + 5 propios) mas los de
`plugins/*/tests/`.

---

## Fase 1 — Crear `gamedev-skills`

### Tarea 1.1: Repo vacio con gitflow y protecciones

```bash
cd C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios
gh repo create jhanva/gamedev-skills --public --description "Skills, agentes y hooks para juegos 2D pixel art con Godot 4 (Claude Code + Codex)" --clone
cd gamedev-skills
git commit --allow-empty -m "chore(repo): iniciar repositorio"
git branch develop
git push -u origin main develop
for b in main develop; do gh api -X PUT repos/jhanva/gamedev-skills/branches/$b/protection --input - <<'EOF'
{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}
EOF
done
```

Verificar: `git branch -r` muestra `origin/main` y `origin/develop`;
`gh api repos/jhanva/gamedev-skills/branches/develop/protection --jq .allow_deletions.enabled` → `false`.

### Tarea 1.2: Rama de trabajo y copia de archivos

```bash
cd C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios/gamedev-skills
git checkout -b feature/importar-desde-ai-skills develop
SRC=../ai-skills
mkdir -p .claude/skills .claude/agents .claude/hooks .agents/skills .agents/plugins .codex/agents .codex/hooks scripts tests docs

for s in rpg-design game-arch pixel-pipeline game-start game-concept art-bible design-system level-brief balance-check sprite-spec tileset-spec palette sound-brief godot-setup scene-design sprint story scope-check playtest smoke-test aseprite-workflows godot-workflows pixellab-workflows; do
  cp -r "$SRC/.claude/skills/$s" .claude/skills/
done
for s in rpg-design game-arch pixel-pipeline game-start game-concept art-bible design-system level-brief balance-check sprite-spec tileset-spec palette sound-brief godot-setup scene-design sprint story scope-check playtest smoke-test; do
  cp -r "$SRC/.agents/skills/$s" .agents/skills/
done
cp -r "$SRC/.claude/agents/gamedev" .claude/agents/
for a in creative-director technical-director game-designer level-designer godot-architect pixel-artist sound-designer qa-analyst producer; do
  cp "$SRC/.codex/agents/$a.toml" .codex/agents/ && cp -r "$SRC/.codex/agents/$a" .codex/agents/
done
cp "$SRC"/.claude/hooks/*.sh .claude/hooks/
cp "$SRC/.claude/settings.json" .claude/
cp "$SRC/.codex/hooks/codex_hooks.py" .codex/hooks/
cp "$SRC/.codex/hooks.json" "$SRC/.codex/config.toml" .codex/
cp -r "$SRC/plugins" "$SRC/pets" .
cp "$SRC/.agents/plugins/marketplace.json" .agents/plugins/
cp "$SRC/.mcp.json" "$SRC/.gitattributes" "$SRC/.gitignore" "$SRC/AGENTS.md" .
cp "$SRC/scripts/bump-codex-model.sh" scripts/
cp "$SRC/tests/test_codex_adaptation.py" tests/
```

Verificar: `ls .claude/skills | wc -l` → `23`; `ls .agents/skills | wc -l` → `20`;
`ls .codex/agents/*.toml | wc -l` → `9`.

### Tarea 1.3: Recortar `scripts/bump-codex-model.sh` a los 9 agentes gamedev

Editar la lista `pinned_in` (comentario de cabecera y array del script) dejando solo:
`creative-director technical-director game-designer level-designer godot-architect pixel-artist
sound-designer qa-analyst producer`. Quitar `prompt-artist`, `reviewer`, `security-auditor`,
`task-implementer` y el parametro `[implementer-model]`.

Verificar: `grep -c 'agents/.*\.toml' scripts/bump-codex-model.sh` → `18` (9 en comentario + 9 en
el array), y `grep -c 'task-implementer\|reviewer\|security-auditor\|prompt-artist'
scripts/bump-codex-model.sh` → `0`.

### Tarea 1.4: Recortar `tests/test_codex_adaptation.py` a los 10 tests gamedev

Borrar `test_secure_scanner_is_native_and_has_fixed_classification`,
`test_secure_scanner_detects_a_token_and_help_is_successful`,
`test_readme_points_to_native_browser_skill_and_codex_hooks`,
`test_browser_helpers_include_cross_platform_fixes` y la constante `SECRET_SCANNER`.
Ajustar `test_model_bump_helper_only_updates_standalone_agent_files` si comprueba nombres de
agentes core.

Verificar: `python -m unittest discover -s tests -q` → `Ran 10 tests ... OK`.
Plugins: `for p in plugins/*/tests; do python -m unittest discover -s "$p" -q; done` → todos `OK`.

### Tarea 1.5: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/codex-adaptation.md`

- `AGENTS.md`: cambiar titulo a `gamedev-skills`; en "Alcance" describir el repo como skills,
  agentes, hooks, plugins y pets para juegos 2D pixel art con Godot 4; en "Skills, agentes y
  hooks" anadir que los hooks de gameplay/assets/GDD son parte del producto. Resto identico.
- `CLAUDE.md`: `@AGENTS.md` + arbol y tablas solo con lo gamedev (copiar las secciones
  "Game development", "Agentes gamedev", "Herramientas externas (MCP)" y hooks del CLAUDE.md
  de `ai-skills`; indicar que `/brainstorm`, `/plan`, `/execute`, `/tdd`, `/verify`, `/review`
  se obtienen de `ai-skills` y se usan en conjunto).
- `README.md`: encabezado con contadores reales (23 skills, 9 agentes, 3 plugins, 2 pets),
  seccion "Uso junto con ai-skills" con los dos `claude --add-dir`.
- `docs/codex-adaptation.md`: copiar y dejar solo la parte de gamedev y plugins.

Verificar: `grep -c 'ai-skills' README.md` ≥ 1 (referencia cruzada);
`grep -n 'tdd\|secure\|browser-control' CLAUDE.md` → solo en la nota de uso conjunto.

### Tarea 1.6: Commit, PR a `develop`, publicacion a `main`

```bash
git add -A
git commit -m "feat: importar skills, agentes, hooks y plugins de game dev desde ai-skills"
git push -u origin feature/importar-desde-ai-skills
gh pr create --base develop --title "feat: importar skills, agentes, hooks y plugins de game dev desde ai-skills" --body-file docs/pr-importar.md
gh pr merge <n> --squash --delete-branch
gh pr create --base main --head develop --title "feat: publicar version inicial de gamedev-skills"
gh pr merge <n> --merge
```

Verificar: `git log --oneline --graph -3 origin/main` muestra el merge commit con `develop`
como antepasado.

---

## Fase 2 — Limpiar `ai-skills`

Rama: `feature/separar-gamedev` desde `develop`. **No empezar hasta que la Fase 1 este en
`main` de `gamedev-skills`**: asi nunca hay un momento sin copia publicada.

### Tarea 2.1: Borrar lo movido

```bash
cd C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios/ai-skills
git checkout develop && git pull --ff-only && git checkout -b feature/separar-gamedev
for s in rpg-design game-arch pixel-pipeline game-start game-concept art-bible design-system level-brief balance-check sprite-spec tileset-spec palette sound-brief godot-setup scene-design sprint story scope-check playtest smoke-test aseprite-workflows godot-workflows pixellab-workflows; do
  git rm -rq ".claude/skills/$s"; [ -d ".agents/skills/$s" ] && git rm -rq ".agents/skills/$s"
done
git rm -rq .claude/agents/gamedev
for a in creative-director technical-director game-designer level-designer godot-architect pixel-artist sound-designer qa-analyst producer; do
  git rm -q ".codex/agents/$a.toml"; git rm -rq ".codex/agents/$a"
done
git rm -q .claude/hooks/validate-gameplay-code.sh .claude/hooks/validate-assets.sh .claude/hooks/check-design-coverage.sh
git rm -rq plugins pets .agents/plugins
git rm -q .mcp.json
```

Verificar: `ls .claude/skills | wc -l` → `21`; `ls .agents/skills | wc -l` → `21`;
`ls .codex/agents/*.toml` → 4 archivos; `ls .claude/hooks` → 3 archivos.

### Tarea 2.2: `session-context.sh` neutro

Reemplazar el contenido por:

```bash
#!/usr/bin/env bash
# SessionStart hook — contexto del repositorio al iniciar

echo "=== Session ==="

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -n "$BRANCH" ] && echo "Branch: $BRANCH"

git log --oneline -5 2>/dev/null | while read -r line; do echo "  $line"; done

MODIFIED=$(git diff --name-only 2>/dev/null)
STAGED=$(git diff --staged --name-only 2>/dev/null)
if [ -n "$MODIFIED" ] || [ -n "$STAGED" ]; then
  echo ""
  echo "Uncommitted changes:"
  [ -n "$STAGED" ] && echo "$STAGED" | while read -r f; do echo "  + $f"; done
  [ -n "$MODIFIED" ] && echo "$MODIFIED" | while read -r f; do echo "  M $f"; done
fi

echo "==============="
exit 0
```

Verificar: `bash .claude/hooks/session-context.sh | head -1` → `=== Session ===`.

### Tarea 2.3: `.claude/settings.json` sin hooks gamedev

Dejar en `hooks`: `SessionStart` → `session-context.sh`; `PreToolUse` (`Bash`) →
`block-env-access.sh`. Eliminar el bloque `PostToolUse` completo y la entrada de
`validate-gameplay-code.sh`. `permissions` no cambia.

Verificar: `python -c "import json;h=json.load(open('.claude/settings.json'))['hooks'];print(sorted(h))"`
→ `['PreToolUse', 'SessionStart']`.

### Tarea 2.4: `codex_hooks.py` y `hooks.json` sin gamedev

En `codex_hooks.py`: borrar `validate_gameplay_code`, `post_edit_checks`,
`resolve_edited_path`, las constantes `HARDCODED_RE`, `UI_IMPORT_RE`, `MOTION_RE`, y sus
entradas en `ACTIONS`. En `session_context` cambiar `"Game dev project context:"` por
`"Repository context:"` y borrar el bloque de `sprint_dir`. Conservar `load_payload`, `emit`,
`deny`, `additional_context`, `tool_command`, `patch_paths`, `is_protected_env_path`,
`pre_tool_policy`, `run_git`, `session_context`, `main`.

En `hooks.json`: eliminar la entrada `PreToolUse` con matcher `^Bash$`
(`validate-gameplay-code`) y todo el bloque `PostToolUse`.

Verificar:
`python .codex/hooks/codex_hooks.py 2>&1 | head -1` → `Usage: codex_hooks.py <pre-tool-policy|session-context>`;
`python -c "import json;h=json.load(open('.codex/hooks.json'))['hooks'];print(sorted(h))"`
→ `['PreToolUse', 'SessionStart']`.

### Tarea 2.5: Tests core

Borrar de `tests/test_codex_adaptation.py`:
`test_gamedev_agents_do_not_implicitly_run_user_skills`,
`test_post_edit_checks_understand_apply_patch_paths`,
`test_post_edit_checks_warn_when_gameplay_has_no_gdd`,
`test_godot_fixes_are_present_in_codex_skills`, `test_planning_fixes_are_consistent`.

Verificar: `python -m unittest discover -s tests -q` → `Ran 10 tests ... OK`.

### Tarea 2.6: `scripts/bump-codex-model.sh` con 4 agentes

Dejar `prompt-artist reviewer security-auditor task-implementer` en cabecera y array.

Verificar: `grep -c 'agents/.*\.toml' scripts/bump-codex-model.sh` → `8`;
`bash scripts/bump-codex-model.sh` sin argumentos imprime el uso y sale con codigo ≠ 0.

### Tarea 2.7: Documentacion

- `CLAUDE.md`: borrar del arbol las 23 skills, `.claude/agents/gamedev/*`, los 3 hooks; borrar
  de la tabla las 23 filas; borrar las secciones "Game development", "Herramientas externas
  (MCP)" y el `/game-start` del flujo; corregir "Para debugging" si referencia gamedev. Anadir
  una linea: "Las skills de game dev viven en `gamedev-skills` y se usan junto con este repo".
- `README.md`: contadores del encabezado (21 skills, 4 agentes Codex, 0 plugins, 0 pets → quitar
  badges de Game Dev, Codex Agents pasa a 4); borrar secciones "Game development", "Plugins",
  "Pets", "Hooks (game dev)", "Herramientas externas"; anadir "Repos relacionados" con enlace a
  `gamedev-skills`.
- `AGENTS.md`: en "Skills, agentes y hooks" borrar la linea de Godot 4; en "Autorizacion" quitar
  PixelLab y marketplaces de la lista de servicios externos; en "Commits" quitar `pets` y
  `plugins` de los alcances.
- `docs/codex-adaptation.md`: borrar el bloque de jerarquia gamedev y menciones a plugins.

Verificar: `grep -rn -i 'godot\|gdd\|pixel\|aseprite\|sprint' README.md CLAUDE.md AGENTS.md docs/codex-adaptation.md`
→ solo la linea que enlaza a `gamedev-skills`.

### Tarea 2.8: Hooks reales en Claude Code

Abrir una sesion nueva de Claude Code en `ai-skills` y comprobar que el SessionStart imprime
`=== Session ===` y que `cat .env` sigue bloqueado por `block-env-access.sh`.

### Tarea 2.9: Commit, PR a `develop`, publicacion a `main`

```bash
git add -A
git commit -m "refactor!: separar game dev en el repositorio gamedev-skills" -m "BREAKING CHANGE: las 23 skills, 9 agentes, 3 hooks, 3 plugins y pets de game dev ya no estan en este repo. Viven en jhanva/gamedev-skills y se instalan por separado."
git push -u origin feature/separar-gamedev
gh pr create --base develop --title "refactor!: separar game dev en el repositorio gamedev-skills" --body-file <descripcion>
gh pr merge <n> --squash --delete-branch
gh pr create --base main --head develop --title "refactor!: publicar ai-skills sin game dev"
gh pr merge <n> --merge
```

---

## Fase 3 — Verificacion cruzada

### Tarea 3.1: Ningun archivo perdido

```bash
cd C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios
comm -13 <(cd ai-skills && git ls-files | sort) <(cd gamedev-skills && git ls-files | sort) > /dev/null
git -C ai-skills ls-files 535160b | sort > /tmp/antes.txt      # main antes de separar
{ git -C ai-skills ls-files; git -C gamedev-skills ls-files; } | sort -u > /tmp/despues.txt
comm -23 /tmp/antes.txt /tmp/despues.txt
```

Verificar: la ultima linea no imprime nada (todo archivo que existia sigue en uno de los dos
repos), salvo `docs/plan-separacion-gamedev.md` si se decide borrarlo al terminar.

### Tarea 3.2: Uso conjunto en un proyecto de juego

En cualquier proyecto Godot local:

```bash
claude --add-dir C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios/ai-skills --add-dir C:/Users/mdmgu/OneDrive/Documentos/johan/repositorios/gamedev-skills
```

Verificar: `/tdd` y `/game-concept` aparecen ambos en el menu `/`.

---

## Auto-revision

- [x] Cada elemento del mapa de archivos tiene una tarea que lo mueve, copia, modifica o borra
- [x] Los 15 tests actuales tienen destino asignado
- [x] Fase 2 no empieza hasta que Fase 1 esta publicada (nunca hay copia unica sin publicar)
- [x] Comandos con rutas reales del entorno actual
- [ ] Pendiente de confirmar por el usuario: nombre `gamedev-skills`, destino de `pets/`
