#!/usr/bin/env bash
# Biblioteca compartida para hooks — JSON parsing con fallback
# Uso: source "$(dirname "$0")/_parse.sh"
#
# Orden de preferencia:
#   1. jq (parser robusto, si esta disponible)
#   2. python / python3 / py (el primero que ejecute de verdad; en Windows
#      "python3" puede ser el alias stub de Microsoft Store, que command -v
#      encuentra pero falla al ejecutar — por eso se valida con una ejecucion real)
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

_PARSE_PYTHON=""

_parse_find_python() {
  [ -n "$_PARSE_PYTHON" ] && return 0
  local cmd
  for cmd in python python3 py; do
    if command -v "$cmd" >/dev/null 2>&1 && "$cmd" -c "import json" >/dev/null 2>&1; then
      _PARSE_PYTHON="$cmd"
      return 0
    fi
  done
  return 1
}

_parse_path() {
  local input="$1" path="$2"
  # Validate path contains only safe characters (alphanumeric, dots, underscores)
  if [[ ! "$path" =~ ^[a-zA-Z0-9_.]+$ ]]; then
    echo "hooks/_parse.sh: invalid path '$path' — only [a-zA-Z0-9_.] allowed" >&2
    return 1
  fi
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r ".${path} // empty" 2>/dev/null
  elif _parse_find_python; then
    printf '%s' "$input" | "$_PARSE_PYTHON" -c "$_PARSE_PY" "$path" 2>/dev/null
  else
    echo "hooks/_parse.sh: requires jq or python (python/python3/py) to parse JSON" >&2
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
