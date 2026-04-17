#!/usr/bin/env bash
# SessionStart hook — muestra contexto del proyecto al iniciar

echo "=== Game Dev Session ==="

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ -n "$BRANCH" ] && echo "Branch: $BRANCH"

# Commits recientes
git log --oneline -5 2>/dev/null | while read -r line; do echo "  $line"; done

# Sprint activo
SPRINT=$(ls -t production/sprints/sprint-*.md 2>/dev/null | head -1)
[ -n "$SPRINT" ] && echo "Sprint: $(basename "$SPRINT" .md)"

# Archivos sin commit
MODIFIED=$(git diff --name-only 2>/dev/null)
STAGED=$(git diff --staged --name-only 2>/dev/null)
if [ -n "$MODIFIED" ] || [ -n "$STAGED" ]; then
  echo ""
  echo "Uncommitted changes:"
  [ -n "$STAGED" ] && echo "$STAGED" | while read -r f; do echo "  + $f"; done
  [ -n "$MODIFIED" ] && echo "$MODIFIED" | while read -r f; do echo "  M $f"; done
fi

echo "========================"
exit 0
