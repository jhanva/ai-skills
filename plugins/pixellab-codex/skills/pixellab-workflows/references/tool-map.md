# Tool Map

## Common PixelLab MCP tools

- `create_character`
  Queue a 4-way or 8-way character generation job.

- `animate_character`
  Queue new animations for an existing character ID.

- `get_character`
  Read character status, preview images, download URL, and pending jobs.

- `create_topdown_tileset`
  Generate top-down Wang tilesets for RPG and map workflows.

- `get_topdown_tileset`
  Inspect a top-down tileset generation job and fetch its outputs.

- `create_sidescroller_tileset`
  Generate platformer terrain tilesets with side-view transitions.

- `get_sidescroller_tileset`
  Inspect a sidescroller tileset job, including example maps when available.

- `create_isometric_tile`
  Generate a single isometric tile or prop.

- `get_isometric_tile`
  Check status and retrieve output for an isometric tile.

- `create_map_object`
  Generate props with transparent backgrounds for maps.

- `get_map_object`
  Check status and retrieve output for a generated map object.

## Recommended pattern

1. Create the asset and capture the returned ID.
2. Queue dependent jobs immediately when applicable.
3. Poll with the matching `get_*` tool until the status is complete.
4. Download or integrate the output into the game project.
