#!/usr/bin/env bash
# PreToolUse hook (Bash) — bloquea lecturas/escrituras a archivos .env
# Exit 0 = allow, Exit 2 = block
#
# Reemplaza reglas de permisos Bash(*>.env*) / Bash(cat *.env*) en settings.json
# que dependen de un matcher fnmatch fragil (sensible a espacios alrededor de `>`).

source "$(dirname "$0")/_parse.sh"

INPUT=$(cat)
COMMAND=$(parse_nested "$INPUT" "tool_input" "command")
[ -z "$COMMAND" ] && exit 0

# Patrones que bloqueamos (regex extendido):
#   - redireccion a .env o .env.*  : `>`, `>>`, `<`, `tee`
#   - lectura explicita de .env    : `cat`, `less`, `more`, `bat`, `head`, `tail`,
#                                    `grep`, `sed`, `awk`
#   - source de .env               : `source`, `.`
#   - copia/mv a .env              : `cp`, `mv`
#
# Se permiten nombres seguros explicitos: .env.example, .env.sample, .env.template
# Estrategia: BORRAR los nombres seguros del comando normalizado y luego aplicar
# los patrones peligrosos sobre el string reducido. Asi `echo a > .env.example
# && echo b > .env` sigue bloqueado (el segundo target sobrevive al borrado).

# Normaliza a una linea con espacios simples para matching.
# Strip de comentarios: solo `#` precedido de whitespace, para no romper
# comandos con `#` entre comillas (p.ej. `echo "x#y" > file`).
NORMALIZED=$(printf '%s' "$COMMAND" | sed 's/[[:space:]]#.*$//' | tr '\n' ' ' | tr -s '[:space:]' ' ')

# Borra nombres seguros SOLO con frontera real: seguido de fin de string o de
# un caracter fuera de [A-Za-z0-9_.]. Asi `.env.example.bak` NO se trata como
# seguro (el `.` siguiente impide el match y el nombre sobrevive al borrado).
NORMALIZED=$(printf '%s' "$NORMALIZED" | sed -E 's/\.env\.(example|sample|template)([^A-Za-z0-9_.]|$)/\2/g')

blocked=""

# Redirecciones: output (`> .env`, `>>.env.local`)
if echo "$NORMALIZED" | grep -qE '(^|[^>])>[>]?\s*\.env\b' ; then
  blocked="write redirect to .env file"
fi

# Input redirection (`< .env`, `<.env.local`)
if echo "$NORMALIZED" | grep -qE '<\s*\.env\b' ; then
  blocked="input redirect from .env file"
fi

# tee a .env
if echo "$NORMALIZED" | grep -qE '\btee(\s+-[aA])?\s+\.env\b' ; then
  blocked="tee to .env file"
fi

# Lectura de .env (cat/less/more/bat/head/tail/grep/sed/awk)
if echo "$NORMALIZED" | grep -qE '\b(cat|less|more|bat|head|tail|grep|sed|awk)\s+[^|]*\.env\b' ; then
  blocked="read of .env file"
fi

# source/dot (`. .env`, `source .env.local`)
if echo "$NORMALIZED" | grep -qE '(\bsource\s+|^\.\s+|\s\.\s+)\.env\b' ; then
  blocked="source of .env file"
fi

# Copia/mv con .env como destino o fuente
if echo "$NORMALIZED" | grep -qE '\b(cp|mv)\s+[^|]*\.env\b' ; then
  blocked="cp/mv with .env path"
fi

if [ -n "$blocked" ]; then
  echo "=== .env access blocked ===" >&2
  echo "  Reason: $blocked" >&2
  echo "  Command: $COMMAND" >&2
  echo "  Allowed filenames: .env.example, .env.sample, .env.template" >&2
  echo "===========================" >&2
  exit 2
fi

exit 0
