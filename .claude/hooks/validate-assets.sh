#!/usr/bin/env bash
# PostToolUse hook (Write|Edit) — valida assets
# Exit 0 = silencioso. Exit 2 = NO bloquea (el tool ya corrio en PostToolUse),
# pero stderr se envia a Claude para que corrija el problema.
# (Exit 1 seria un error no bloqueante visible solo al usuario — no usar.)

source "$(dirname "$0")/_parse.sh"

INPUT=$(cat)
FILE_PATH=$(parse_nested "$INPUT" "tool_input" "file_path")
FILE_PATH=$(echo "$FILE_PATH" | sed 's|\\|/|g')

# Solo archivos en assets/
echo "$FILE_PATH" | grep -qE '(^|/)assets/' || exit 0

FILENAME=$(basename "$FILE_PATH")
WARNINGS=""
ERRORS=""

# Warning: naming convention (lowercase_snake) — reportado a Claude via exit 2
if echo "$FILENAME" | grep -qE '[A-Z[:space:]-]'; then
  WARNINGS="$WARNINGS\n  NAMING: $FILE_PATH — use lowercase_snake_case (got: $FILENAME)"
fi

# Error: JSON valido en assets/data/ — reportado a Claude via exit 2
if echo "$FILE_PATH" | grep -qE '(^|/)assets/data/.*\.json$' && [ -f "$FILE_PATH" ]; then
  PYTHON_CMD=""
  for cmd in python python3 py; do
    command -v "$cmd" >/dev/null 2>&1 && PYTHON_CMD="$cmd" && break
  done
  if [ -n "$PYTHON_CMD" ]; then
    "$PYTHON_CMD" -m json.tool "$FILE_PATH" >/dev/null 2>&1 || \
      ERRORS="$ERRORS\n  JSON: $FILE_PATH is not valid JSON"
  fi
fi

[ -n "$WARNINGS" ] && echo -e "=== Asset Warnings ===$WARNINGS\n=====================" >&2
[ -n "$ERRORS" ] && echo -e "=== Asset ERRORS ===$ERRORS\n====================" >&2

# Exit 2: stderr llega a Claude (PostToolUse no bloquea, el tool ya corrio)
if [ -n "$WARNINGS" ] || [ -n "$ERRORS" ]; then
  exit 2
fi

exit 0
