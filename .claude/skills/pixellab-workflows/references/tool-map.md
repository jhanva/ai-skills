# Tool Map

## Tools comunes del MCP de PixelLab

- `create_character`
  Encola un job de generacion de personaje 4-way o 8-way.

- `animate_character`
  Encola nuevas animaciones para un character ID existente.

- `get_character`
  Lee estado del personaje, preview images, download URL y jobs pendientes.

- `create_topdown_tileset`
  Genera tilesets top-down Wang para workflows de RPG y mapas.

- `get_topdown_tileset`
  Inspecciona un job de tileset top-down y obtiene sus outputs.

- `create_sidescroller_tileset`
  Genera tilesets de terreno de plataformas con transiciones side-view.

- `get_sidescroller_tileset`
  Inspecciona un job de tileset sidescroller, incluyendo mapas de ejemplo cuando esten disponibles.

- `create_isometric_tile`
  Genera un tile o prop isometrico individual.

- `get_isometric_tile`
  Verifica estado y obtiene output de un tile isometrico.

- `create_map_object`
  Genera props con fondos transparentes para mapas.

- `get_map_object`
  Verifica estado y obtiene output de un objeto de mapa generado.

## Patron recomendado

1. Crear el asset y capturar el ID retornado.
2. Encolar jobs dependientes inmediatamente cuando aplique.
3. Hacer poll con el tool `get_*` correspondiente hasta que el status sea complete.
4. Descargar o integrar el output en el proyecto del juego.
