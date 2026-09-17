# Albedo Pet

Paquete portable de la custom pet final de Albedo para Codex.

Contenido:

- `pet.json`: manifiesto que Codex usa para registrar la pet
- `spritesheet.webp`: atlas final de la animacion

## Instalar La Pet

1. Crea el directorio destino si no existe:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\\.codex\\pets\\albedo"
```

2. Copia `pet.json` y `spritesheet.webp`:

```powershell
Copy-Item ".\\pets\\albedo\\pet.json" "$HOME\\.codex\\pets\\albedo\\pet.json" -Force
Copy-Item ".\\pets\\albedo\\spritesheet.webp" "$HOME\\.codex\\pets\\albedo\\spritesheet.webp" -Force
```

Estructura final esperada:

```text
~/.codex/pets/albedo/
  pet.json
  spritesheet.webp
```

Si Codex estaba abierto, reinicialo para que vuelva a cargar las pets custom.

## Notas

- Esta carpeta guarda solo la version final aprobada.
- `pet.json` usa `spritesheetPath: "spritesheet.webp"`, asi que ambos archivos deben quedarse juntos.
