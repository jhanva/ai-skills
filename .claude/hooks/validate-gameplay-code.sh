#!/usr/bin/env bash
# PreToolUse hook (Bash: git commit) — valida codigo gameplay
# ADVISORY ONLY: NO bloquea el commit. Emite los warnings como JSON en stdout
# ({"systemMessage": "..."}) con exit 0, para que el usuario los vea sin
# bloquear. (En PreToolUse, exit 2 bloquearia el tool call — no usar aqui.)

source "$(dirname "$0")/_parse.sh"

INPUT=$(cat)
COMMAND=$(parse_nested "$INPUT" "tool_input" "command")

# Solo procesar git commit (tambien `cd x && git commit`, `git -C dir commit`, etc.)
echo "$COMMAND" | grep -qE '(^|&&|;|\|)[[:space:]]*git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit' || exit 0

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
    # Asignaciones ([+\-*/]= o = simple); excluye comparaciones `==`
    if grep -qE '(position|velocity|rotation)[[:space:]]*([+*/-]=|=[^=])' "$file" 2>/dev/null; then
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
  # stdout JSON con exit 0: no bloquea el commit y el usuario ve el warning.
  MSG=$(printf '%b' "=== Gameplay Code Warnings ===$WARNINGS\n===========================")
  # Encode JSON con jq o python (mismos requisitos que _parse.sh)
  if command -v jq >/dev/null 2>&1; then
    JSON_MSG=$(printf '%s' "$MSG" | jq -Rs .)
  elif _parse_find_python; then
    JSON_MSG=$(printf '%s' "$MSG" | "$_PARSE_PYTHON" -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  else
    JSON_MSG=""
  fi
  [ -n "$JSON_MSG" ] && printf '{"systemMessage": %s}\n' "$JSON_MSG"
fi

exit 0
