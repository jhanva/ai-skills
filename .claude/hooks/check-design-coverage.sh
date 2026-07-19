#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) — advierte si gameplay code no tiene GDD
# Exit 2 con warning = NO bloquea (PostToolUse corre despues del tool),
# pero stderr se envia a Claude para que lo vea. Exit 0 = sin hallazgos.

source "$(dirname "$0")/_parse.sh"

INPUT=$(cat)
FILE_PATH=$(parse_nested "$INPUT" "tool_input" "file_path")
FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Solo archivos en src/gameplay/
echo "$FILE_PATH" | grep -qE '(^|/)src/gameplay/' || exit 0

# Extraer nombre del sistema: src/gameplay/{system}/...
SYSTEM=$(echo "$FILE_PATH" | grep -oE 'src/gameplay/[^/]+' | sed 's|src/gameplay/||')
[ -z "$SYSTEM" ] && exit 0

# Buscar GDD correspondiente
if [ ! -f "design/gdd/${SYSTEM}.md" ] && [ ! -f "design/gdd/${SYSTEM}-system.md" ]; then
  echo "=== Design Coverage Warning ===" >&2
  echo "  Code in src/gameplay/$SYSTEM/ has no design doc." >&2
  echo "  Expected: design/gdd/${SYSTEM}.md" >&2
  echo "  Run /design-system to create one." >&2
  echo "===============================" >&2
  # Exit 2: stderr llega a Claude (PostToolUse no bloquea)
  exit 2
fi

exit 0
