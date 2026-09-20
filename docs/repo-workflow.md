# Flujo del repositorio

## Gitflow

`main` contiene lo publicado y `develop` lo integrado pendiente de publicar. Todo
cambio nace desde la rama permanente actualizada y entra por pull request.

| Origen | Destino | Integracion | Borrar origen |
|---|---|---|---|
| `feature/`, `fix/`, `agent/` | `develop` | squash | si |
| `hotfix/` | `main` | squash | no |
| `main` tras hotfix | `develop` | merge commit | no aplica |
| `develop` | `main` | merge commit | nunca |

Antes de ramificar: `git fetch --prune`, `git checkout develop` y
`git pull --ff-only`. Una rama desechable solo se elimina cuando su contenido esta
en `develop`.

## Commits y pull requests

Los commits usan Conventional Commits en espanol:

```text
<tipo>(<alcance>): <descripcion imperativa>
```

Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`
y `revert`. La primera linea usa minusculas, no termina en punto y no supera 72
caracteres. No se agregan trailers ni atribuciones de asistentes.

Un pull request explica que cambia, por que, archivos afectados, pruebas y runtimes
tocados. Antes de integrarlo:

1. la rama no tiene conflictos con el destino
2. `python -m unittest discover -s tests` pasa
3. no incluye settings locales, caches, temporales ni credenciales
4. la documentacion y versiones reflejan skills, agentes o hooks modificados
5. usa el modo de integracion de la tabla anterior

## Versiones y catalogos

Cada skill pertenece a un solo plugin. Al anadir, mover o cambiar una skill se
actualiza la version de los dos manifests del plugin y la entrada versionada del
marketplace de Claude Code. El marketplace nativo de Codex obtiene la version del
`plugin.json` portable y mantiene el mismo catalogo de nombres y fuentes.

Cuando este disponible, ejecutar tambien `claude plugin validate .`.

## Archivos y salidas

- texto UTF-8 sin BOM
- LF por defecto y en `.sh`; CRLF en `.ps1`
- temporales fuera del repositorio
- no versionar `.claude/settings.local.json`, `__pycache__/`, secretos ni entornos
- un unico archivo vigente por asunto; no usar sufijos `copia`, `nuevo`, `final`, `v2`
