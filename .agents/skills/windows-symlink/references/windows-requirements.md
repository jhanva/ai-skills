# Windows Symlink Requirements

Lee este archivo solo cuando necesites validar prerequisitos del sistema o explicar por que un symlink no funciona en Windows.

## Requisitos minimos

Para que un symlink de archivo funcione bien en Windows, normalmente necesitas:

- Windows 10/11 moderno
- volumen NTFS
- Git con `core.symlinks=true`
- capacidad real de crear symlinks:
  - shell elevada como administrador, o
  - Developer Mode activo para el usuario

## Checks utiles

- `git config --global core.symlinks`
- PowerShell: `New-Item -ItemType SymbolicLink`
- CMD: `mklink`
- Developer Mode:
  - registry: `HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock`
  - clave: `AllowDevelopmentWithoutDevLicense=1`

## Fallos comunes

### Git deja un archivo de texto con la ruta del target

Normalmente significa:

- `core.symlinks` estaba desactivado al clonar o hacer checkout
- o Windows no podia crear symlinks en ese momento

### `New-Item -ItemType SymbolicLink` falla con permiso denegado

Normalmente significa:

- falta shell elevada
- o Developer Mode esta apagado

### El link existe pero el repo sigue mal

Suele significar:

- el entorno ya soporta symlinks, pero el checkout anterior ya quedo materializado como archivo plano

## Symlink vs junction vs hard link

No son lo mismo:

- symlink: sirve para archivos y directorios; es lo que Git espera para entradas `120000`
- junction: solo directorios; no reemplaza un symlink de archivo
- hard link: solo mismo volumen y mismo archivo; tampoco representa una entrada Git `120000`

Para repos Git con symlinks de archivo, junctions y hard links no son sustitutos reales.
