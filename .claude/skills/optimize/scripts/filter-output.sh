#!/usr/bin/env bash
# filter-output.sh — Patrones de filtrado para reducir output antes de que entre al contexto
#
# Uso: command | ./filter-output.sh [tipo]
# Tipos: test, build, lint, log, general
#
# Ejemplo:
#   npm test 2>&1 | ./filter-output.sh test
#   npm run build 2>&1 | ./filter-output.sh build
#   cat app.log | ./filter-output.sh log

set -euo pipefail

TYPE="${1:-general}"
MAX_LINES="${2:-100}"

case "$TYPE" in
  test)
    # Solo fallos y resumen
    grep -E '(FAIL|FAILED|ERROR|error:|✗|✕|BROKEN|panic|AssertionError|expected .* to|not ok)' \
      | head -n "$MAX_LINES"
    echo "---"
    echo "[filtrado: solo fallos, max $MAX_LINES lineas]"
    ;;

  build)
    # Solo errores y warnings criticos
    grep -i -E '(error|fatal|failed|cannot find|not found|undefined reference)' \
      | grep -v -i 'warning:.*unused' \
      | head -n "$MAX_LINES"
    echo "---"
    echo "[filtrado: solo errores de build, max $MAX_LINES lineas]"
    ;;

  lint)
    # Solo errores, ignorar warnings y info
    grep -E '(error|✗|✕)' \
      | grep -v -i 'warning' \
      | head -n "$MAX_LINES"
    echo "---"
    echo "[filtrado: solo errores de lint, max $MAX_LINES lineas]"
    ;;

  log)
    # Solo errores y excepciones recientes
    tail -500 \
      | grep -i -E '(error|exception|fatal|panic|critical|traceback|stack trace)' \
      | head -n "$MAX_LINES"
    echo "---"
    echo "[filtrado: solo errores de log, max $MAX_LINES lineas]"
    ;;

  general|*)
    # Quitar lineas vacias, limitar longitud
    grep -v '^[[:space:]]*$' \
      | head -n "$MAX_LINES"
    echo "---"
    echo "[filtrado: max $MAX_LINES lineas]"
    ;;
esac
