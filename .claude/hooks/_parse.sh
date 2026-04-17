#!/usr/bin/env bash
# Biblioteca compartida para hooks — JSON parsing con fallback
# Uso: source "$(dirname "$0")/_parse.sh"

parse_field() {
  local input="$1" field="$2"
  if command -v jq >/dev/null 2>&1; then
    echo "$input" | jq -r ".$field // empty" 2>/dev/null
  else
    echo "$input" | grep -oE "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | \
      sed "s/\"${field}\"[[:space:]]*:[[:space:]]*\"//;s/\"$//"
  fi
}

parse_nested() {
  local input="$1" parent="$2" field="$3"
  if command -v jq >/dev/null 2>&1; then
    echo "$input" | jq -r ".$parent.$field // empty" 2>/dev/null
  else
    echo "$input" | grep -oE "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | \
      sed "s/\"${field}\"[[:space:]]*:[[:space:]]*\"//;s/\"$//"
  fi
}
