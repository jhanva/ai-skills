---
name: git-identity
description: >
  Audita y configura identidades Git separadas por directorio, host, CLI y
  SSH key en macOS, Linux o Windows. Valida includeIf, shell guards,
  pre-commit hooks y SSH config. Soporta hosts distintos y mismo host con
  aliases SSH. Modos: audit (read-only), setup.
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Git Identity — Auditoria y configuracion de identidades Git separadas

## Uso

- Invocacion explicita con `/git-identity`.
- Usa lecturas puntuales para revisar config: `git config`, `git remote -v`, y lectura directa de archivos concretos.
- Modo por defecto: `audit`.
- Si el prompt menciona `setup`, ejecutar el flujo de configuracion.
- `audit` es read-only.
- `setup` modifica archivos fuera del repo como `~/.gitconfig`, `~/.ssh/config`, perfiles de shell y hooks globales. Antes de escribir cualquier archivo fuera del workspace, explica que vas a tocar y pide confirmacion del usuario.

## Objetivo

Gestionar la separacion de identidades Git en una misma maquina, por ejemplo:
- cuenta personal en GitHub
- cuenta corporativa en GitLab
- dos cuentas distintas en el mismo host, como GitHub personal + GitHub work
- aislamiento por directorio
- proteccion adicional por shell wrappers, pre-commit y SSH keys

Funciona en macOS, Linux y Windows.

## Flujo

1. Determinar modo.
2. Detectar el OS y resolver rutas.
3. Ejecutar auditoria completa.
4. Si el modo es `setup`, configurar solo las capas faltantes o rotas.
5. Volver a auditar y reportar el resultado.

## Determinar modo

- Si el prompt contiene `setup`, usa modo `setup`.
- Si el prompt esta vacio o contiene `check`, `audit` o `review`, usa modo `audit`.

## Paso 1: Detectar OS y rutas

Detecta el sistema con:

```bash
uname -s 2>/dev/null || echo Windows
```

Rutas esperadas:

| Recurso | macOS / Linux | Windows |
|---|---|---|
| Git config global | `~/.gitconfig` | `$env:USERPROFILE\.gitconfig` |
| Git config sandbox | `~/.gitconfig-sandbox` | `$env:USERPROFILE\.gitconfig-sandbox` |
| SSH config | `~/.ssh/config` | `$env:USERPROFILE\.ssh\config` |
| Shell profile | `~/.zshrc` o `~/.bashrc` | resultado de `echo $PROFILE` |
| Hooks globales | resultado de `git config core.hooksPath` | resultado de `git config core.hooksPath` |

### Detectar escenario

Antes de auditar o configurar, clasifica el caso:

- **Hosts diferentes**: los remotes o entradas SSH usan hosts reales distintos, por ejemplo `github.com` y `gitlab.com`.
- **Mismo host**: las entradas SSH usan aliases distintos pero con el mismo `HostName`, por ejemplo `github.com-work` y `github.com-personal`, ambos apuntando a `github.com`.

Para detectarlo:
- inspecciona `git remote -v`
- lee el archivo SSH config
- si ves aliases distintos que comparten `HostName`, trata el caso como **mismo host**

## Modo `audit`

Solo lectura. No modifica nada.

### Paso 2: Identidad actual

Ejecuta:

```bash
git config user.name
git config user.email
git remote -v
git config core.hooksPath
pwd
```

Reporta:

```markdown
## Identidad actual

| Campo | Valor |
|---|---|
| Nombre | ... |
| Email | ... |
| Remote | ... |
| Hooks path | ... |
| Directorio | ... |
| OS | ... |
```

### Paso 3: Auditar las 4 capas

#### Capa 1 — `includeIf`

- Lee el gitconfig global.
- Verifica que exista un bloque `includeIf` apuntando al directorio sandbox.
- Verifica que el archivo referenciado exista.
- Verifica que el archivo sandbox tenga un bloque `[user]` con el email correcto.

#### Capa 2 — shell guards

- En macOS/Linux, lee `~/.zshrc` o `~/.bashrc`.
- En Windows, lee el PowerShell profile.
- En **hosts diferentes**, busca wrappers o funciones para `gh` y `glab` que bloqueen el uso segun el directorio.
- En **mismo host**, busca wrappers o funciones para `gh` que hagan auto-switch por directorio usando `GH_TOKEN`.

#### Capa 3 — pre-commit hook

- Obten `core.hooksPath`.
- Verifica que exista `pre-commit` en esa ruta.
- Verifica que contenga logica de validacion entre remote host y `user.email`.
- En macOS/Linux, verifica permisos de ejecucion.

#### Capa 4 — SSH keys

- Lee el archivo de SSH config.
- Verifica entradas separadas por host o por alias.
- Verifica `IdentityFile` distinta por host o alias.
- En **mismo host**, verifica que cada alias tenga `HostName` apuntando al host real.
- Verifica que cada archivo de llave exista.

### Paso 4: Reporte

Usa este formato:

```markdown
## Auditoria de identidad Git

### Estado: [OK | ADVERTENCIA | ERROR]

| Capa | Estado | Detalle |
|---|---|---|
| 1. includeIf | ... | ... |
| 2. Shell guards | ... | ... |
| 3. Pre-commit hook | ... | ... |
| 4. SSH keys | ... | ... |
```

Criterios:
- `OK`: las 4 capas verificadas
- `ADVERTENCIA`: 1-2 capas con issues menores
- `ERROR`: falta una capa critica o esta mal configurada

## Modo `setup`

Lee `references/setup.md` solo si el modo es `setup`.

### Reglas de seguridad

- No reconfigures a ciegas
- Corre `audit` primero
- Cambia solo capas faltantes o rotas
- Antes de escribir fuera del repo, resume archivos a tocar y pide confirmacion

### Flujo

1. Confirmar datos faltantes de cuenta principal y sandbox
2. Clasificar el caso: hosts distintos o mismo host con aliases SSH
3. Cargar `references/setup.md` y configurar solo las capas necesarias
4. Re-ejecutar `audit`
5. Reportar estado final por capa

### Capas a cubrir

- `includeIf`
- shell guards o auto-switch de CLI/token
- pre-commit hook global
- SSH keys y aliases si aplica

### Entregable

- resumen de cambios por capa
- comandos de verificacion ejecutados
- nota final para recargar shell si fue necesario

## Entrada esperada

Toma del prompt del usuario:
- el modo (`audit` o `setup`)
- la ruta sandbox si la menciona
- hosts, emails o CLIs si ya vienen especificados
- aliases SSH y usernames si el caso es mismo host
