#!/usr/bin/env bash
# Biblioteca compartida para hooks — JSON parsing con fallback
# Uso: source "$(dirname "$0")/_parse.sh"
#
# Orden de preferencia:
#   1. jq (parser robusto, si esta disponible)
#   2. python3 (disponible en macOS y la mayoria de distros)
#   3. error: aborta con mensaje a stderr y devuelve empty
#
# NO se usa regex-over-string como fallback: un parser "naive" no distingue
# objetos padres, y un mismo nombre de campo puede aparecer en tool_input y
# tool_response del mismo payload.

_PARSE_PY='
import json, sys
path = [p for p in sys.argv[1].split(".") if p]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
node = data
for key in path:
    if isinstance(node, dict) and key in node:
        node = node[key]
    else:
        sys.exit(0)
if node is None:
    sys.exit(0)
if isinstance(node, (dict, list)):
    print(json.dumps(node))
else:
    print(node)
'

_parse_path() {
  local input="$1" path="$2"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r ".${path} // empty" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$input" | python3 -c "$_PARSE_PY" "$path" 2>/dev/null
  else
    echo "hooks/_parse.sh: requires jq or python3 to parse JSON" >&2
    return 1
  fi
}

parse_field() {
  local input="$1" field="$2"
  _parse_path "$input" "$field"
}

parse_nested() {
  local input="$1" parent="$2" field="$3"
  _parse_path "$input" "${parent}.${field}"
}
