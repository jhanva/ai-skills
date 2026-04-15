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

### Regla de seguridad

- No reconfigures a ciegas.
- Primero corre la auditoría.
- Solo cambia capas faltantes o rotas.
- Antes de escribir fuera del repo, resume los archivos a modificar y pide confirmación.

### Paso 2: Recopilar datos

Pide o confirma:

```text
Cuenta principal
- Nombre completo
- Email
- Host
- CLI
- SSH key path

Cuenta sandbox
- Email
- Directorio sandbox
- Host
- CLI
- SSH key path
```

Si el escenario es **mismo host**, también confirma:

```text
- Host real compartido
- Alias principal
- Alias sandbox
- Username principal
- Username sandbox
```

Si algún valor ya se puede inferir de la configuración actual, muéstralo como valor detectado y pide confirmación breve en vez de preguntar desde cero.

### Paso 3: Ejecutar auditoría primero

Corre el flujo `audit` y detecta qué capas están:
- OK
- faltantes
- rotas

### Paso 4: Configurar capas faltantes

#### Capa 1 — `includeIf`

macOS/Linux:

```ini
[user]
    name = {NOMBRE}
    email = {EMAIL_PRINCIPAL}

[includeIf "gitdir:{DIRECTORIO_SANDBOX}/"]
    path = ~/.gitconfig-sandbox
```

Archivo sandbox:

```ini
[user]
    name = {NOMBRE}
    email = {EMAIL_SANDBOX}
```

Windows:

```ini
[includeIf "gitdir:C:/Users/{USER}/projects/sandbox/"]
    path = ~/.gitconfig-sandbox
```

Usa `git rev-parse --show-toplevel` para verificar el formato de ruta que Git espera.

#### Capa 2 — shell guards

##### Escenario hosts diferentes

macOS/Linux:

```bash
# Identity isolation: {HOST_SANDBOX} ({CLI_SANDBOX}) vs {HOST_PRINCIPAL} ({CLI_PRINCIPAL})
{CLI_SANDBOX}() {
    if [[ "$PWD" != "$HOME/{DIRECTORIO_SANDBOX_RELATIVO}"* ]]; then
        echo "{CLI_SANDBOX} blocked: only available inside ~/{DIRECTORIO_SANDBOX_RELATIVO}/" >&2
        return 1
    fi
    command {CLI_SANDBOX} "$@"
}

{CLI_PRINCIPAL}() {
    if [[ "$PWD" == "$HOME/{DIRECTORIO_SANDBOX_RELATIVO}"* ]]; then
        echo "{CLI_PRINCIPAL} blocked: not available inside ~/{DIRECTORIO_SANDBOX_RELATIVO}/" >&2
        return 1
    fi
    command {CLI_PRINCIPAL} "$@"
}
```

Windows PowerShell:

```powershell
function {CLI_SANDBOX} {
    $sandboxPath = Join-Path $env:USERPROFILE "{DIRECTORIO_SANDBOX_RELATIVO}"
    if (-not $PWD.Path.StartsWith($sandboxPath)) {
        Write-Error "{CLI_SANDBOX} blocked: only available inside ~/{DIRECTORIO_SANDBOX_RELATIVO}/"
        return
    }
    $exe = (Get-Command {CLI_SANDBOX} -CommandType Application -ErrorAction Stop).Source
    & $exe @args
}

function {CLI_PRINCIPAL} {
    $sandboxPath = Join-Path $env:USERPROFILE "{DIRECTORIO_SANDBOX_RELATIVO}"
    if ($PWD.Path.StartsWith($sandboxPath)) {
        Write-Error "{CLI_PRINCIPAL} blocked: not available inside ~/{DIRECTORIO_SANDBOX_RELATIVO}/"
        return
    }
    $exe = (Get-Command {CLI_PRINCIPAL} -CommandType Application -ErrorAction Stop).Source
    & $exe @args
}
```

##### Escenario mismo host

Si ambas cuentas usan el mismo host y el mismo CLI, no bloquees `gh`: haz auto-switch de `GH_TOKEN` por directorio.

macOS/Linux:

```bash
# GitHub multi-account: auto-switch gh auth by directory
if [[ -f ~/.config/gh/tokens ]]; then
    source ~/.config/gh/tokens
fi

gh() {
    if [[ "$PWD" == "$HOME/{DIRECTORIO_SANDBOX_RELATIVO}"* ]]; then
        GH_TOKEN="$GH_TOKEN_SANDBOX" command gh "$@"
    else
        GH_TOKEN="$GH_TOKEN_PRINCIPAL" command gh "$@"
    fi
}
```

Archivo de tokens:

```bash
export GH_TOKEN_PRINCIPAL="ghp_..."
export GH_TOKEN_SANDBOX="ghp_..."
```

Luego:

```bash
chmod 600 ~/.config/gh/tokens
```

Windows PowerShell:

```powershell
$tokenFile = Join-Path $env:USERPROFILE ".config\\gh\\tokens.ps1"
if (Test-Path $tokenFile) { . $tokenFile }

function gh {
    $sandboxPath = Join-Path $env:USERPROFILE "{DIRECTORIO_SANDBOX_RELATIVO}"
    if ($PWD.Path.StartsWith($sandboxPath)) {
        $env:GH_TOKEN = $env:GH_TOKEN_SANDBOX
    } else {
        $env:GH_TOKEN = $env:GH_TOKEN_PRINCIPAL
    }
    $exe = (Get-Command gh -CommandType Application -ErrorAction Stop).Source
    & $exe @args
}
```

Tokens:

```powershell
$env:GH_TOKEN_PRINCIPAL = "ghp_..."
$env:GH_TOKEN_SANDBOX = "ghp_..."
```

Recuerda:
- nunca commitear esos tokens
- si un token se compromete, revocarlo inmediatamente

#### Capa 3 — pre-commit hook global

Si `core.hooksPath` no existe:

macOS/Linux:

```bash
mkdir -p ~/.config/git/hooks
git config --global core.hooksPath ~/.config/git/hooks
```

Windows:

```powershell
New-Item -Path "$env:USERPROFILE\.config\git\hooks" -ItemType Directory -Force
git config --global core.hooksPath "$env:USERPROFILE/.config/git/hooks"
```

Hook:

```bash
#!/bin/bash
remote_url=$(git remote get-url origin 2>/dev/null)
user_email=$(git config user.email)

if [[ "$remote_url" == *"{HOST_SANDBOX}"* ]] && [[ "$user_email" != "{EMAIL_SANDBOX}" ]]; then
    echo "COMMIT BLOCKED: {HOST_SANDBOX} repo but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_SANDBOX}" >&2
    exit 1
fi

if [[ "$remote_url" == *"{HOST_PRINCIPAL}"* ]] && [[ "$user_email" != "{EMAIL_PRINCIPAL}" ]]; then
    echo "COMMIT BLOCKED: {HOST_PRINCIPAL} repo but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_PRINCIPAL}" >&2
    exit 1
fi

local_hook="$(git rev-parse --git-dir 2>/dev/null)/hooks/pre-commit"
if [[ -x "$local_hook" ]]; then
    exec "$local_hook" "$@"
fi
```

Luego:

```bash
chmod +x ~/.config/git/hooks/pre-commit
```

En Windows, Git for Windows ejecuta hooks bash sin extensión; usa el mismo contenido.

##### Escenario mismo host

Si ambas cuentas usan el mismo host:

- **Estrategia A recomendada**: validar por alias SSH en el remote.
- **Estrategia B fallback**: validar por directorio del repo si aún no existen aliases.

Estrategia A:

```bash
#!/bin/bash
remote_url=$(git remote get-url origin 2>/dev/null)
user_email=$(git config user.email)

if [[ "$remote_url" == *"{HOST}-{ALIAS_SANDBOX}"* ]] && [[ "$user_email" != "{EMAIL_SANDBOX}" ]]; then
    echo "COMMIT BLOCKED: {ALIAS_SANDBOX} repo but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_SANDBOX}" >&2
    exit 1
fi

if [[ "$remote_url" == *"{HOST}-{ALIAS_PRINCIPAL}"* ]] && [[ "$user_email" != "{EMAIL_PRINCIPAL}" ]]; then
    echo "COMMIT BLOCKED: {ALIAS_PRINCIPAL} repo but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_PRINCIPAL}" >&2
    exit 1
fi

local_hook="$(git rev-parse --git-dir 2>/dev/null)/hooks/pre-commit"
if [[ -x "$local_hook" ]]; then
    exec "$local_hook" "$@"
fi
```

Estrategia B:

```bash
#!/bin/bash
user_email=$(git config user.email)
repo_dir=$(git rev-parse --show-toplevel 2>/dev/null)

if [[ "$repo_dir" == "$HOME/{DIRECTORIO_SANDBOX_RELATIVO}"* ]] && [[ "$user_email" != "{EMAIL_SANDBOX}" ]]; then
    echo "COMMIT BLOCKED: repo in sandbox but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_SANDBOX}" >&2
    exit 1
fi

if [[ "$repo_dir" != "$HOME/{DIRECTORIO_SANDBOX_RELATIVO}"* ]] && [[ "$user_email" != "{EMAIL_PRINCIPAL}" ]]; then
    echo "COMMIT BLOCKED: repo outside sandbox but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_PRINCIPAL}" >&2
    exit 1
fi

local_hook="$(git rev-parse --git-dir 2>/dev/null)/hooks/pre-commit"
if [[ -x "$local_hook" ]]; then
    exec "$local_hook" "$@"
fi
```

#### Capa 4 — SSH keys

No generes ni registres claves automáticamente sin confirmación del usuario.

Si faltan, muestra instrucciones:

```bash
ssh-keygen -t ed25519 -C "{EMAIL_PRINCIPAL}" -f {SSH_KEY_PRINCIPAL}
ssh-keygen -t ed25519 -C "{EMAIL_SANDBOX}" -f {SSH_KEY_SANDBOX}
```

SSH config:

```text
Host {HOST_PRINCIPAL}
  HostName {HOST_PRINCIPAL}
  User git
  IdentityFile {SSH_KEY_PRINCIPAL}

Host {HOST_SANDBOX}
  HostName {HOST_SANDBOX}
  User git
  IdentityFile {SSH_KEY_SANDBOX}
```

Verificación:

```bash
ssh -T git@{HOST_SANDBOX}
ssh -T git@{HOST_PRINCIPAL}
```

##### Escenario mismo host

Si ambas cuentas usan el mismo host real, se requieren aliases SSH distintos:

```text
Host {HOST}-{ALIAS_PRINCIPAL}
  HostName {HOST}
  User git
  IdentityFile {SSH_KEY_PRINCIPAL}

Host {HOST}-{ALIAS_SANDBOX}
  HostName {HOST}
  User git
  IdentityFile {SSH_KEY_SANDBOX}
```

Ejemplo:

```text
Host github.com-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_work

Host github.com-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_personal
```

En este escenario:
- los remotes deben usar el alias, no el host real
- SSH por sí solo no puede distinguir dos cuentas del mismo host sin aliases

Actualización de remote:

```bash
git remote set-url origin git@{HOST}-{ALIAS_SANDBOX}:{USERNAME_SANDBOX}/repo.git
```

Verificación:

```bash
ssh -T git@{HOST}-{ALIAS_PRINCIPAL}
ssh -T git@{HOST}-{ALIAS_SANDBOX}
```

### Paso 5: Verificación final

Vuelve a correr `audit` y reporta:

```markdown
## Setup completado

| Capa | Accion |
|---|---|
| 1. includeIf | [Creada / Ya existia / Reparada] |
| 2. Shell guards | [Creada / Ya existia / Reparada] |
| 3. Pre-commit hook | [Creada / Ya existia / Reparada] |
| 4. SSH keys | [Instrucciones mostradas / Ya existia] |
```

Recarga sugerida:
- macOS/Linux: `source ~/.zshrc`
- Windows PowerShell: `. $PROFILE`

## Entrada esperada

Toma del prompt del usuario:
- el modo (`audit` o `setup`)
- la ruta sandbox si la menciona
- hosts, emails o CLIs si ya vienen especificados
- aliases SSH y usernames si el caso es mismo host
