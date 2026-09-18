#!/usr/bin/env bash
# PostToolUse hook (Edit|Write|MultiEdit) — corre el detector de UI sobre el
# archivo editado y, si hay hallazgos, los devuelve como additionalContext.
# Nunca bloquea: exit 0 siempre. El payload llega por stdin y lo parsea detect.py.
#
# Python varia entre maquinas (python, python3, py); se valida con una
# ejecucion real porque en Windows "python3" puede ser el stub de la Store.

SCRIPT="$(dirname "$0")/../scripts/detect.py"

for candidate in python python3 py; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys" >/dev/null 2>&1; then
    if [ "$candidate" = "py" ]; then
      exec "$candidate" -3 "$SCRIPT" --hook
    fi
    exec "$candidate" "$SCRIPT" --hook
  fi
done

exit 0
