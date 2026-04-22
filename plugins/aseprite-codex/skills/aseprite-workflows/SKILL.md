---
name: aseprite-workflows
description: Use this skill when the user wants to inspect `.aseprite` files, export sprite sheets or frame sequences, or automate Aseprite with Lua scripts from Codex. Prefer the bundled MCP tools over GUI automation.
---

# Aseprite Workflows

Use this skill for repeatable `Aseprite` tasks from Codex.

## First move

1. If the binary path is unknown, call `aseprite_detect`.
2. If the task mentions layers, tags, slices, or "what is inside this sprite?", call `aseprite_inspect`.
3. Choose the narrowest export tool that fits:
   - `aseprite_export_sprite_sheet` for atlas + JSON workflows
   - `aseprite_export_frames` for frame sequences, tags, or layer splits
   - `aseprite_run_script` only when built-in export flags are not enough

## Path rules

- Prefer absolute paths.
- If the prompt uses repo-relative paths, pass `workspace_root` so the MCP server resolves them correctly.
- Use `preview=true` to validate a command before large exports.

## Guardrails

- Prefer structured MCP tools over `Computer Use` for anything repeatable.
- Keep outputs close to the source asset unless the user asks for a different destination.
- When a workflow needs tags/layers and the file has not been inspected yet, inspect first instead of guessing names.

## Load on demand

- Read `references/tool-map.md` for common recipes and argument mapping.
