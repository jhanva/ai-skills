#!/usr/bin/env bash
# PreToolUse hook (Bash: git commit) — valida codigo gameplay
# ADVISORY ONLY: imprime warnings a stderr pero siempre hace exit 0.
# Si quieres convertirlo en bloqueante, cambia el `exit 0` final por `exit 2`
# y documenta el comportamiento en el README.

source "$(dirname "$0")/_parse.sh"

INPUT=$(cat)
COMMAND=$(parse_nested "$INPUT" "tool_input" "command")

# Solo procesar git commit
echo "$COMMAND" | grep -qE '^git[[:space:]]+commit' || exit 0

STAGED=$(git diff --cached --name-only 2>/dev/null)
[ -z "$STAGED" ] && exit 0

WARNINGS=""

# Check 1: hardcoded gameplay values en src/gameplay/
GAMEPLAY_FILES=$(echo "$STAGED" | grep -E '^src/gameplay/')
if [ -n "$GAMEPLAY_FILES" ]; then
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    HITS=$(grep -nE '(damage|health|speed|rate|chance|cost|duration|mana|stamina)[[:space:]]*[:=][[:space:]]*[0-9]' "$file" 2>/dev/null)
    [ -n "$HITS" ] && WARNINGS="$WARNINGS\n  HARDCODED: $file — use data files:\n$HITS"
  done <<< "$GAMEPLAY_FILES"
fi

# Check 2: missing delta time
CODE_FILES=$(echo "$STAGED" | grep -E '^src/.*\.(gd|cs)$')
if [ -n "$CODE_FILES" ]; then
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    if grep -qE '(position|velocity|rotation)[[:space:]]*[+\-*/]?=' "$file" 2>/dev/null; then
      if ! grep -qE 'delta' "$file" 2>/dev/null; then
        WARNINGS="$WARNINGS\n  DELTA: $file modifies position/velocity without delta time"
      fi
    fi
  done <<< "$CODE_FILES"
fi

# Check 3: gameplay importing UI
if [ -n "$GAMEPLAY_FILES" ]; then
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    HITS=$(grep -nE '(from|import|preload|load).*["\x27].*ui[/\\]' "$file" 2>/dev/null)
    [ -n "$HITS" ] && WARNINGS="$WARNINGS\n  LAYER: $file imports UI code directly — use signals:\n$HITS"
  done <<< "$GAMEPLAY_FILES"
fi

if [ -n "$WARNINGS" ]; then
  echo -e "=== Gameplay Code Warnings ===$WARNINGS\n===========================" >&2
fi

exit 0
