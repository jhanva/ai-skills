# Tool Map

## When to use each tool

- `aseprite_detect`
  Use when the user asks whether Aseprite is installed, gives a custom binary path, or a command fails because the binary cannot be found.

- `aseprite_inspect`
  Use before exports that depend on `layer`, `tag`, or slices. It returns `layers`, `tags`, `slices`, and the raw `meta` block from Aseprite JSON output.

- `aseprite_export_sprite_sheet`
  Use for atlas exports, metadata JSON, tileset exports, and packed sheet workflows.

- `aseprite_export_frames`
  Use for `save-as` workflows: frame sequences, one-frame thumbnails, tag splits, and layer splits.

- `aseprite_run_script`
  Use for custom Lua automation when the CLI flags alone are not expressive enough.

## Common recipes

### Packed sprite sheet with JSON

- tool: `aseprite_export_sprite_sheet`
- required args:
  - `sprite_path`
  - `sheet_path`
- common optional args:
  - `data_path`
  - `sheet_type="packed"`
  - `ignore_empty=true`
  - `merge_duplicates=false`
  - `trim=true`
  - `extrude=true`

### Export only one animation tag

- inspect first to confirm the tag name
- then call `aseprite_export_frames` with:
  - `sprite_path`
  - `output_path`
  - `tag`
  - optional `split_layers`

### Dry run before exporting

- pass `preview=true`
- use this before wide exports or when the user asks to "show me the command first"

## Notes

- `split_layers`, `split_tags`, and `ignore-layer` must be decided before the sprite is opened, so the MCP server always places those flags before the input file.
- For repo-relative asset paths, pass `workspace_root` to avoid resolving paths relative to the plugin directory.
