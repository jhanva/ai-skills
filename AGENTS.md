# Reglas para agentes

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
