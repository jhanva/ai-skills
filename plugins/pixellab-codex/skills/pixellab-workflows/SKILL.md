---
name: pixellab-workflows
description: Use this skill when the user wants PixelLab asset generation tools inside Codex through the official PixelLab MCP server.
---

# PixelLab Workflows

Use this skill when PixelLab MCP tools are installed in Codex.

## First move

1. If PixelLab tools such as `create_character` or `create_topdown_tileset` are visible, use them directly.
2. If the tools are not visible, tell the user PixelLab MCP is not configured or authenticated yet.
3. Prefer the smallest asset operation that fits the task:
   - `create_character` then `animate_character` for directional characters
   - `create_topdown_tileset` or `create_sidescroller_tileset` for terrain kits
   - `create_isometric_tile` for individual isometric assets
   - `create_map_object` for map props

## Workflow pattern

- PixelLab creation tools are asynchronous: they return IDs first, then you poll with the corresponding `get_*` tool.
- Queue follow-up jobs immediately when the API supports it, then inspect status later.
- Keep download URLs and generated IDs in the conversation when they matter for the next step.

## Guardrails

- Do not try to fake PixelLab with raw `curl` if the MCP tools are already available.
- If Codex has no PixelLab MCP tools loaded, explain that the plugin or API token still needs setup.
- Prefer explicit size, directions, and style constraints over vague prompts for game-ready outputs.

## Load on demand

- Read `references/tool-map.md` when you need a compact map of the official MCP tools.
