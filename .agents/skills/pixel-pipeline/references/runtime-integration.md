# Pixel Pipeline — Runtime Integration

Lee este archivo solo cuando definas atlas, memoria o integracion en engine.

## Atlas

No empaquetes todo en un solo atlas. Separar por contexto suele funcionar mejor:

- `characters`
- `enemies`
- `tiles`
- `ui`
- `effects`

## Budget rapido

- atlas `1024x1024 RGBA` ~= 4MB
- atlas `2048x2048 RGBA` ~= 16MB

En mobile, conviene mantener el peak total en un rango razonable para la escena activa.

## Palette swap

Tiene sentido cuando quieres:

- variantes de enemigos
- facciones
- tiers de equipo
- tintes de status effect

Si no aporta mucho, no fuerces shader; a veces assets separados son suficientes.

## UI pixel art

Checklist minima:

- 9-patch o equivalente para panels
- pixel font con filtering correcto
- tamanos alineados al grid base

## Workflow minimo de export

1. producir assets con naming consistente
2. exportar sprite sheets o frames
3. empaquetar atlas
4. generar o mantener metadata de animacion
5. validar filtering, padding y pivots
