---
name: git-identity
description: "Audita y configura identidades Git separadas por directorio, host, CLI y SSH key en macOS, Linux o Windows. Úsala cuando el usuario quiera revisar o aislar cuentas Git/CLI/SSH, validar includeIf, shell guards, hooks o SSH config, o configurar esa separación desde cero, tanto para hosts distintos como para el mismo host con aliases SSH."
---

# Git Identity — Auditoria y configuracion de identidades Git separadas

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$git-identity`.
- Modo por defecto: `audit`.
- Si el prompt menciona `setup`, ejecutar el flujo de configuración.
- `audit` es read-only.
- `setup` modifica archivos fuera del repo como `~/.gitconfig`, `~/.ssh/config`, perfiles de shell y hooks globales. Antes de escribir cualquier archivo fuera del workspace, explica qué vas a tocar y pide confirmación del usuario.

## Objetivo

Gestionar la separación de identidades Git en una misma máquina, por ejemplo:
- cuenta personal en GitHub
- cuenta corporativa en GitLab
- dos cuentas distintas en el mismo host, como GitHub personal + GitHub work
- aislamiento por directorio
- protección adicional por shell wrappers, pre-commit y SSH keys

Funciona en macOS, Linux y Windows.

## Flujo

1. Determinar modo.
2. Detectar el OS y resolver rutas.
3. Ejecutar auditoría completa.
4. Si el modo es `setup`, configurar solo las capas faltantes o rotas.
5. Volver a auditar y reportar el resultado.

## Determinar modo

- Si el prompt contiene `setup`, usa modo `setup`.
- Si el prompt está vacío o contiene `check`, `audit` o `review`, usa modo `audit`.

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
- En **hosts diferentes**, busca wrappers o funciones para `gh` y `glab` que bloqueen el uso según el directorio.
- En **mismo host**, busca wrappers o funciones para `gh` que hagan auto-switch por directorio usando `GH_TOKEN`.

#### Capa 3 — pre-commit hook

- Obtén `core.hooksPath`.
- Verifica que exista `pre-commit` en esa ruta.
- Verifica que contenga lógica de validación entre remote host y `user.email`.
- En macOS/Linux, verifica permisos de ejecución.

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
- `ERROR`: falta una capa crítica o está mal configurada

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
