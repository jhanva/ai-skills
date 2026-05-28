# The Lich King Pet

Paquete portable de una custom pet para Codex.

Contenido:

- `pet.json`: manifiesto que Codex usa para registrar la pet
- `spritesheet.webp`: atlas final de la animacion
- `qa/contact-sheet.png`: hoja de control visual de todas las filas/frames
- `qa/validation.json`: validacion tecnica del atlas final

## Requisitos

Para **usar la pet** en otra PC:

- Codex instalado
- acceso al directorio `~/.codex/pets/`

Para **regenerar o editar** la pet con el mismo workflow:

- Codex instalado
- skill `hatch-pet`
- skill de sistema `imagegen` disponible en Codex

## Instalar La Pet En Otra PC

1. Copia esta carpeta completa a la otra maquina.
2. Crea el directorio destino si no existe:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\\.codex\\pets\\the-lich-king"
```

3. Copia `pet.json` y `spritesheet.webp` a ese directorio:

```powershell
Copy-Item ".\\pets\\the-lich-king\\pet.json" "$HOME\\.codex\\pets\\the-lich-king\\pet.json" -Force
Copy-Item ".\\pets\\the-lich-king\\spritesheet.webp" "$HOME\\.codex\\pets\\the-lich-king\\spritesheet.webp" -Force
```

Estructura final esperada:

```text
~/.codex/pets/the-lich-king/
  pet.json
  spritesheet.webp
```

Si Codex estaba abierto, reinicialo para que vuelva a cargar las pets custom.

## Instalar La Skill `hatch-pet`

La pet ya funciona sin reinstalar la skill. La skill solo hace falta si quieres regenerar, reparar o crear variantes.

Instalacion desde Codex:

```text
$skill-installer hatch-pet
```

Si prefieres el helper script directamente:

```powershell
python "$HOME\\.codex\\skills\\.system\\skill-installer\\scripts\\install-skill-from-github.py" --repo openai/skills --path skills/.curated/hatch-pet
```

Despues de instalar la skill, reinicia Codex para que aparezca en la sesion.

## Verificacion Rapida

Puedes revisar estos archivos antes de moverla:

- `qa/contact-sheet.png`: confirma que las 9 filas de animacion se ven correctas
- `qa/validation.json`: confirma atlas `1536x1872`, `RGBA`, y sin residuos en pixeles transparentes

## Regenerar O Editar

Prompt base usado para esta pet:

- nombre: `The Lich King`
- fantasy: rey no-muerto helado, armadura pesada negra/azulada, ojos azules brillantes
- prop: hacha maldita estilo `Shadowmourne`
- tono: oscuro, serio, dominante
- estilo: `pixel`, chibi, legible a tamano pequeno

Workflow recomendado:

1. Instala `hatch-pet`.
2. Invoca `$hatch-pet` con referencias y prompt.
3. Guarda el nuevo `spritesheet.webp`.
4. Sustituye este archivo y actualiza `pet.json` solo si cambian `id`, `displayName` o descripcion.

## Notas

- `pet.json` usa `spritesheetPath: "spritesheet.webp"`, asi que ambos archivos deben quedarse juntos.
- La carpeta `qa/` no es obligatoria para que Codex use la pet, pero si es util para transportar y revisar calidad.
