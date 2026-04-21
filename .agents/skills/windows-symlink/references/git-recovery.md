# Git Symlink Recovery on Windows

Lee este archivo solo cuando el entorno ya soporte symlinks, pero el repo actual siga roto.

## Sintoma tipico

El indice Git contiene entradas `120000`, pero en el working tree aparecen como archivos normales cuyo contenido es la ruta destino del link.

## Orden de recuperacion recomendado

1. Confirmar que el entorno ya puede crear symlinks.
2. Confirmar `git config --global core.symlinks true`.
3. Revisar si el repo esta limpio con `git status --short`.
4. Preferir fresh clone.

## Por que fresh clone es la opcion segura

Porque evita:

- tocar un working tree con cambios locales
- mezclar archivos planos viejos con links nuevos
- dejar el repo en un estado medio reparado

## Repair in-place

Solo considerarlo si:

- el usuario lo pidio explicitamente
- el repo esta limpio
- ya esta confirmado que Windows puede crear symlinks reales

Opciones:

- `git reset --hard HEAD`
- re-checkout completo

Ambas pueden descartar cambios locales. Nunca las uses si `git status --short` no esta limpio.

## Fallback si Windows no puede soportar symlinks

Si el equipo o la politica del OS no permite symlinks reales:

- para scripts pequenos, usar copia real o shim en la capa Codex
- para links de directorio, evaluar junction solo si el caso lo permite
- no asumas que junction o hard link arreglan un symlink de archivo que Git trackea como `120000`

## Nota para este repo

Hay al menos un caso real de symlink de archivo en:

- `.agents/skills/secure/scripts/scan-secrets.py`

Si Windows no puede materializarlo como symlink real, el fallback portable es un archivo real o shim en la capa Codex, no un junction.
