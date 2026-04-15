# Reglas para agentes

## Codex

### Adaptacion del repositorio

- Este repositorio tiene dos capas en paralelo:
  - `.claude/` conserva la implementacion original pensada para Claude Code
  - `.agents/skills/`, `.codex/agents/` y `.codex/config.toml` contienen la adaptacion nativa para Codex
- No modifiques `.claude/` salvo que el usuario lo pida de forma explicita. Para trabajo orientado a Codex, edita solo la capa nueva.
- En Codex, la invocacion explicita de skills es con `$skill`, no con `/skill`.

### Traduccion de herramientas heredadas

- Si una instruccion heredada menciona herramientas de Claude, traducela asi:
  - `Read` / `Grep` / `Glob` / `Bash` -> `rg`, `rg --files`, `find`, `sed -n`, shell puntual
  - `Agent` -> agentes built-in (`worker`, `explorer`) o agentes custom en `.codex/agents/`
  - `Edit` / `Write` -> la herramienta nativa de patch del entorno de Codex (por ejemplo `apply_patch` cuando exista)
  - `WebFetch` / `WebSearch` -> browsing web segun la politica del entorno

### Reglas globales para Codex

- Haz lecturas minimas y puntuales antes de abrir archivos completos
- Usa `multi_tool_use.parallel` cuando varias lecturas o inspecciones sean independientes
- Filtra output ruidoso de comandos antes de traerlo a contexto
- No declares exito sin una verificacion fresca con comandos reales

## Commits

Todos los commits deben seguir [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

### Formato

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types permitidos

| Type | Cuando usarlo |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Correccion de bug |
| `docs` | Solo cambios en documentacion |
| `style` | Formateo, punto y coma faltante, etc. (no cambia logica) |
| `refactor` | Cambio de codigo que no agrega feature ni arregla bug |
| `perf` | Mejora de rendimiento |
| `test` | Agregar o corregir tests |
| `build` | Cambios en sistema de build o dependencias |
| `ci` | Cambios en configuracion de CI |
| `chore` | Tareas de mantenimiento (no afectan src ni test) |
| `revert` | Revertir un commit anterior |

### Reglas

- El type es **obligatorio** y en minusculas
- El scope es **opcional**, entre parentesis: `feat(auth): add 2FA support`
- La description es **obligatoria**, en minusculas, sin punto final, imperativa
- Breaking changes se indican con `!` antes de `:` o con footer `BREAKING CHANGE:`
- El body es opcional, separado por una linea en blanco
- Los footers son opcionales, separados por una linea en blanco
- `Co-Authored-By:` va siempre como footer cuando aplique

### Ejemplos

```
feat(secure): add docker security patterns

fix(tdd): correct test anti-pattern detection

docs: update README with /secure usage

refactor(debug): simplify root cause tracing flow

feat(execute)!: change subagent dispatch protocol

BREAKING CHANGE: subagents now receive task text directly instead of file paths
```
