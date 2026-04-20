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
SAFE='\.env\.(example|sample|template)(\b|$)'

# Normaliza a una linea con espacios simples para matching
# Strip shell comments to avoid false positives on `.env` mentioned in comments
NORMALIZED=$(printf '%s' "$COMMAND" | sed 's/#.*$//' | tr '\n' ' ' | tr -s '[:space:]' ' ')

# Extrae el target potencial. Si coincide con .env.* seguro, permitir.
# Chequeamos por tokens de interes.
blocked=""

# Redirecciones: output (`> .env`, `>>.env.local`) and input (`< .env`)
if echo "$NORMALIZED" | grep -qE '(^|[^>])>[>]?\s*\.env\b' ; then
  if ! echo "$NORMALIZED" | grep -qE ">\s*$SAFE" ; then
    blocked="write redirect to .env file"
  fi
fi

# Input redirection (`< .env`, `<.env.local`)
if echo "$NORMALIZED" | grep -qE '<\s*\.env\b' ; then
  if ! echo "$NORMALIZED" | grep -qE "<\s*$SAFE" ; then
    blocked="input redirect from .env file"
  fi
fi

# tee a .env
if echo "$NORMALIZED" | grep -qE '\btee(\s+-[aA])?\s+\.env\b' ; then
  if ! echo "$NORMALIZED" | grep -qE "\btee[^|]*$SAFE" ; then
    blocked="tee to .env file"
  fi
fi

# Lectura de .env (cat/less/more/bat/head/tail/grep/sed/awk)
if echo "$NORMALIZED" | grep -qE '\b(cat|less|more|bat|head|tail|grep|sed|awk)\s+[^|]*\.env\b' ; then
  if ! echo "$NORMALIZED" | grep -qE "\b(cat|less|more|bat|head|tail|grep|sed|awk)\s+[^|]*$SAFE" ; then
    blocked="read of .env file"
  fi
fi

# source/dot (`. .env`, `source .env.local`)
if echo "$NORMALIZED" | grep -qE '(\bsource\s+|^\.\s+|\s\.\s+)\.env\b' ; then
  if ! echo "$NORMALIZED" | grep -qE "(\bsource\s+|^\.\s+|\s\.\s+)$SAFE" ; then
    blocked="source of .env file"
  fi
fi

# Copia/mv con .env como destino o fuente
if echo "$NORMALIZED" | grep -qE '\b(cp|mv)\s+[^|]*\.env\b' ; then
  if ! echo "$NORMALIZED" | grep -qE "\b(cp|mv)\s+[^|]*$SAFE" ; then
    blocked="cp/mv with .env path"
  fi
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
