#!/usr/bin/env bash
# Actualiza el pin de modelo de Codex en todos los agentes a la vez.
#
# Uso:
#   scripts/bump-codex-model.sh <default-model> [implementer-model]
#
# Ejemplo:
#   scripts/bump-codex-model.sh gpt-5.5
#   scripts/bump-codex-model.sh gpt-5.5 gpt-5.3
#
# Actualiza:
#   - .codex/config.toml ([agents.models])
#   - .codex/agents/prompt-artist.toml
#   - .codex/agents/reviewer.toml
#   - .codex/agents/security-auditor.toml
#   - .codex/agents/task-implementer.toml  (usa implementer-model si se pasa)

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <default-model> [implementer-model]" >&2
  exit 2
fi

DEFAULT_MODEL="$1"
IMPL_MODEL="${2:-$DEFAULT_MODEL}"

cd "$(dirname "$0")/.."

python3 - "$DEFAULT_MODEL" "$IMPL_MODEL" <<'PY'
import re, sys, pathlib

default_model, impl_model = sys.argv[1], sys.argv[2]

default_agents = [
    ".codex/agents/prompt-artist.toml",
    ".codex/agents/reviewer.toml",
    ".codex/agents/security-auditor.toml",
    ".codex/agents/creative-director.toml",
    ".codex/agents/technical-director.toml",
    ".codex/agents/game-designer.toml",
    ".codex/agents/level-designer.toml",
    ".codex/agents/godot-architect.toml",
    ".codex/agents/pixel-artist.toml",
    ".codex/agents/sound-designer.toml",
    ".codex/agents/qa-analyst.toml",
    ".codex/agents/producer.toml",
]
impl_agents = [".codex/agents/task-implementer.toml"]

def bump(path: str, model: str) -> None:
    p = pathlib.Path(path)
    text = p.read_text()
    new, n = re.subn(r'^(model\s*=\s*)"[^"]+"', rf'\1"{model}"', text, count=1, flags=re.M)
    if n == 0:
        print(f"  warn: no model line in {path}")
        return
    if new == text:
        print(f"  noop (already {model}): {path}")
        return
    p.write_text(new)
    print(f"  updated {path} -> {model}")

print(f"Setting default model to {default_model} and implementer to {impl_model}")
for a in default_agents:
    bump(a, default_model)
for a in impl_agents:
    bump(a, impl_model)

# Update .codex/config.toml too
cfg = pathlib.Path(".codex/config.toml")
text = cfg.read_text()
text = re.sub(r'^(default\s*=\s*)"[^"]+"', rf'\1"{default_model}"', text, count=1, flags=re.M)
text = re.sub(r'^(implementer\s*=\s*)"[^"]+"', rf'\1"{impl_model}"', text, count=1, flags=re.M)
cfg.write_text(text)
print("  updated .codex/config.toml")
PY

echo "Done. Review changes with: git diff .codex/"
