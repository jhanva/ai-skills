# Git Identity — Auditoria y configuracion de cuentas git separadas

Gestiona la separacion de identidades git en esta maquina.
Soporta dos escenarios:
- **Hosts diferentes:** GitHub personal + GitLab empresarial (o cualquier combinacion)
- **Mismo host:** dos cuentas de GitHub (personal + trabajo)

Funciona en macOS, Linux y Windows.

**Argumento:** $ARGUMENTS

---

## Determinar modo

- Si `$ARGUMENTS` contiene "setup": ejecutar **modo SETUP**
- Si `$ARGUMENTS` esta vacio o contiene "check" o "audit": ejecutar **modo AUDIT**

---

## Modo AUDIT

Verifica que la configuracion existente esta intacta. Solo lectura, no modifica nada.

### Paso 1: Detectar OS y rutas

Ejecutar `uname -s 2>/dev/null || echo Windows` para detectar el OS.

Rutas segun OS:

| Recurso | macOS / Linux | Windows |
|---|---|---|
| Git config global | `~/.gitconfig` | `$env:USERPROFILE\.gitconfig` |
| Git config override | `~/.gitconfig-sandbox` | `$env:USERPROFILE\.gitconfig-sandbox` |
| SSH config | `~/.ssh/config` | `$env:USERPROFILE\.ssh\config` |
| Shell profile | `~/.zshrc` o `~/.bashrc` | Resultado de `echo $PROFILE` en PowerShell |
| Git hooks globales | Resultado de `git config core.hooksPath` | Idem |

### Paso 2: Identidad actual

Ejecutar:

```
git config user.name
git config user.email
git remote -v
git config core.hooksPath
```

Mostrar como tabla:

```
## Identidad actual

| Campo      | Valor       |
|------------|-------------|
| Nombre     | [resultado] |
| Email      | [resultado] |
| Remote     | [resultado] |
| Hooks path | [resultado] |
| Directorio | [pwd]       |
| OS         | [detectado] |
```

### Paso 3: Detectar escenario

Leer SSH config y gitconfig para determinar el escenario:

- Si hay entradas SSH con HostName diferentes (github.com + gitlab.com) → **hosts diferentes**
- Si hay entradas SSH con alias diferentes pero mismo HostName (github.com-personal + github.com-work, ambos apuntando a github.com) → **mismo host**
- Si no hay SSH config o no es concluyente, inferir del remote actual

### Paso 4: Auditar las 4 capas

Leer cada archivo de config adaptando rutas al OS detectado.

**Capa 1 — includeIf (auto-switch de identidad):**
- Leer gitconfig global
- Verificar que existe directiva `includeIf` apuntando al directorio sandbox
- Verificar que el archivo referenciado existe y tiene `[user]` con email correcto
- Funciona IGUAL en ambos escenarios (se basa en directorio, no en host)

**Capa 2 — Shell guards (CLI bloqueado o auto-switch por directorio):**

*Escenario hosts diferentes (CLIs distintos: gh vs glab):*
- Buscar funciones wrapper que bloquean el CLI equivocado por directorio

*Escenario mismo host (mismo CLI: gh):*
- Buscar funcion wrapper de `gh` que cambia token/auth segun directorio
- Verificar que las variables de entorno con tokens estan definidas
  (o que gh tiene multiples cuentas autenticadas)

**Capa 3 — Pre-commit hook (validacion email vs remote):**
- Obtener ruta de `git config core.hooksPath`
- Verificar que `pre-commit` existe en esa ruta
- Verificar que contiene logica de validacion email vs remote

*Escenario hosts diferentes:*
- El hook debe comparar host real del remote (github.com, gitlab.com)

*Escenario mismo host:*
- El hook debe comparar el alias SSH del remote (github.com-personal, github.com-work)
  O debe comparar por directorio (si esta dentro de sandbox → email X)

- En macOS/Linux: verificar permisos de ejecucion con `ls -la`

**Capa 4 — SSH keys (llave por host o por alias):**
- Leer SSH config

*Escenario hosts diferentes:*
- Verificar entradas separadas por host real (Host github.com, Host gitlab.com)

*Escenario mismo host:*
- Verificar entradas con alias (Host github.com-personal, Host github.com-work)
- Verificar que ambas tienen HostName apuntando al host real
- Verificar que los IdentityFile son diferentes

- Verificar que los archivos de llave existen

### Paso 5: Reporte

```
## Auditoria de identidad Git

### Escenario: [Hosts diferentes / Mismo host]
### Estado: [OK | ADVERTENCIA | ERROR]

| Capa | Estado | Detalle |
|------|--------|---------|
| 1. includeIf      | [OK/FALTA/ERROR] | [detalle] |
| 2. Shell guards   | [OK/FALTA/ERROR] | [detalle] |
| 3. Pre-commit hook| [OK/FALTA/ERROR] | [detalle] |
| 4. SSH keys       | [OK/FALTA/ERROR] | [detalle] |
```

Criterios:
- **OK**: Las 4 capas verificadas
- **ADVERTENCIA**: 1-2 capas con issues menores
- **ERROR**: Capa critica falta o esta mal configurada

---

## Modo SETUP

Configura la separacion de identidades desde cero o repara capas faltantes.

### Paso 1: Detectar OS

Igual que en modo audit. Determinar rutas segun OS.

### Paso 2: Recopilar datos de las cuentas

Preguntar al usuario la informacion de ambas cuentas. Si alguna ya esta configurada
(detectar del gitconfig global), mostrarla como default.

```
## Cuenta principal (global, fuera de sandbox)
- Nombre completo: [ej: Johan Vargas]
- Email: [ej: johan.vargas@empresa.com]
- Host: [ej: gitlab.com]
- Username en el host: [ej: johan-vargas]
- CLI: [ej: glab]  (preguntar solo si host es diferente)
- SSH key path: [ej: ~/.ssh/id_ed25519]

## Cuenta secundaria (sandbox)
- Email: [ej: jarbey.mejia@gmail.com]
- Directorio sandbox: [ej: ~/projects/sandbox]
- Host: [ej: github.com]
- Username en el host: [ej: jhanva]
- CLI: [ej: gh]  (preguntar solo si host es diferente)
- SSH key path: [ej: ~/.ssh/id_github]
```

Dejar que el usuario confirme o cambie cada valor antes de continuar.

### Paso 3: Detectar escenario

Comparar el host de ambas cuentas:

- Si `HOST_PRINCIPAL != HOST_SANDBOX` → **escenario HOSTS DIFERENTES**
- Si `HOST_PRINCIPAL == HOST_SANDBOX` → **escenario MISMO HOST**

Informar al usuario que escenario se detecto y que implica.

### Paso 4: Ejecutar auditoria

Correr el modo AUDIT internamente para detectar que capas ya existen.
Solo configurar las capas faltantes o rotas. No tocar las que estan OK.

### Paso 5: Configurar capas faltantes

Para cada capa que falte, pedir confirmacion antes de aplicar.

---

#### Capa 1: includeIf (identica en ambos escenarios)

**macOS / Linux:**

Verificar si `~/.gitconfig` tiene `[user]` con email principal. Si no:

```ini
[user]
    name = {NOMBRE}
    email = {EMAIL_PRINCIPAL}
```

Verificar si tiene `includeIf`. Si no:

```ini
[includeIf "gitdir:{DIRECTORIO_SANDBOX}/"]
    path = ~/.gitconfig-sandbox
```

Crear `~/.gitconfig-sandbox` si no existe:

```ini
[user]
    name = {NOMBRE}
    email = {EMAIL_SANDBOX}
```

**Windows:**

Misma logica. En el `includeIf` usar forward slashes (git en Windows las acepta):

```ini
[includeIf "gitdir:C:/Users/{USER}/projects/sandbox/"]
    path = ~/.gitconfig-sandbox
```

Verificar formato con `git rev-parse --show-toplevel`.

---

#### Capa 2: Shell guards

##### Escenario HOSTS DIFERENTES (CLIs distintos)

**macOS / Linux (zsh/bash):**

Agregar al final de `~/.zshrc` (o `~/.bashrc`):

```bash
# Identity isolation: {HOST_SANDBOX} ({CLI_SANDBOX}) vs {HOST_PRINCIPAL} ({CLI_PRINCIPAL})
{CLI_SANDBOX}() {
    if [[ "$PWD" != "$HOME/{SANDBOX_RELATIVO}"* ]]; then
        echo "{CLI_SANDBOX} blocked: only available inside ~/{SANDBOX_RELATIVO}/" >&2
        return 1
    fi
    command {CLI_SANDBOX} "$@"
}

{CLI_PRINCIPAL}() {
    if [[ "$PWD" == "$HOME/{SANDBOX_RELATIVO}"* ]]; then
        echo "{CLI_PRINCIPAL} blocked: not available inside ~/{SANDBOX_RELATIVO}/" >&2
        return 1
    fi
    command {CLI_PRINCIPAL} "$@"
}
```

**Windows (PowerShell):**

```powershell
# Identity isolation: {HOST_SANDBOX} ({CLI_SANDBOX}) vs {HOST_PRINCIPAL} ({CLI_PRINCIPAL})
function {CLI_SANDBOX} {
    $sandboxPath = Join-Path $env:USERPROFILE "{SANDBOX_RELATIVO}"
    if (-not $PWD.Path.StartsWith($sandboxPath)) {
        Write-Error "{CLI_SANDBOX} blocked: only available inside ~/{SANDBOX_RELATIVO}/"
        return
    }
    $exe = (Get-Command {CLI_SANDBOX} -CommandType Application -ErrorAction Stop).Source
    & $exe @args
}

function {CLI_PRINCIPAL} {
    $sandboxPath = Join-Path $env:USERPROFILE "{SANDBOX_RELATIVO}"
    if ($PWD.Path.StartsWith($sandboxPath)) {
        Write-Error "{CLI_PRINCIPAL} blocked: not available inside ~/{SANDBOX_RELATIVO}/"
        return
    }
    $exe = (Get-Command {CLI_PRINCIPAL} -CommandType Application -ErrorAction Stop).Source
    & $exe @args
}
```

##### Escenario MISMO HOST (mismo CLI: gh)

Ambas cuentas usan `gh`. No se puede bloquear el CLI — se necesita auto-switch de contexto.

**Estrategia:** Usar la variable de entorno `GH_TOKEN` para que `gh` use la cuenta correcta
segun el directorio. Los tokens se almacenan en variables de entorno del shell profile
(no hardcodeados en el wrapper).

**macOS / Linux (zsh/bash):**

Agregar al final de `~/.zshrc` (o `~/.bashrc`):

```bash
# GitHub multi-account: auto-switch gh auth by directory
# Tokens are stored in ~/.config/gh/tokens (not in this file)
if [[ -f ~/.config/gh/tokens ]]; then
    source ~/.config/gh/tokens
fi

gh() {
    if [[ "$PWD" == "$HOME/{SANDBOX_RELATIVO}"* ]]; then
        GH_TOKEN="$GH_TOKEN_SANDBOX" command gh "$@"
    else
        GH_TOKEN="$GH_TOKEN_PRINCIPAL" command gh "$@"
    fi
}
```

Crear `~/.config/gh/tokens` con permisos restrictivos:

```bash
# Tokens de GitHub — NO commitear este archivo
# Generar en: GitHub > Settings > Developer settings > Personal access tokens
export GH_TOKEN_PRINCIPAL="ghp_..."   # cuenta {USERNAME_PRINCIPAL}
export GH_TOKEN_SANDBOX="ghp_..."     # cuenta {USERNAME_SANDBOX}
```

Luego: `chmod 600 ~/.config/gh/tokens`

**Windows (PowerShell):**

Agregar al PowerShell profile:

```powershell
# GitHub multi-account: auto-switch gh auth by directory
$tokenFile = Join-Path $env:USERPROFILE ".config\gh\tokens.ps1"
if (Test-Path $tokenFile) { . $tokenFile }

function gh {
    $sandboxPath = Join-Path $env:USERPROFILE "{SANDBOX_RELATIVO}"
    if ($PWD.Path.StartsWith($sandboxPath)) {
        $env:GH_TOKEN = $env:GH_TOKEN_SANDBOX
    } else {
        $env:GH_TOKEN = $env:GH_TOKEN_PRINCIPAL
    }
    $exe = (Get-Command gh -CommandType Application -ErrorAction Stop).Source
    & $exe @args
}
```

Crear `$env:USERPROFILE\.config\gh\tokens.ps1`:

```powershell
# Tokens de GitHub — NO commitear este archivo
$env:GH_TOKEN_PRINCIPAL = "ghp_..."   # cuenta {USERNAME_PRINCIPAL}
$env:GH_TOKEN_SANDBOX = "ghp_..."     # cuenta {USERNAME_SANDBOX}
```

**Instrucciones para generar tokens:**

```
Para cada cuenta de GitHub:
1. Ir a https://github.com/settings/tokens
2. Generate new token (classic)
3. Seleccionar scopes: repo, read:org, workflow
4. Copiar el token generado (empieza con ghp_)
5. Pegarlo en el archivo de tokens correspondiente

IMPORTANTE:
- El archivo de tokens tiene permisos 600 (solo el usuario puede leerlo)
- NUNCA commitear tokens — verificar que esta en .gitignore global
- Si un token se compromete, revocarlo inmediatamente en GitHub
```

---

#### Capa 3: Pre-commit hook

Determinar la ruta de hooks. Si `core.hooksPath` no esta configurado:

**macOS / Linux:**
```bash
mkdir -p ~/.config/git/hooks
git config --global core.hooksPath ~/.config/git/hooks
```

**Windows:**
```powershell
New-Item -Path "$env:USERPROFILE\.config\git\hooks" -ItemType Directory -Force
git config --global core.hooksPath "$env:USERPROFILE/.config/git/hooks"
```

##### Escenario HOSTS DIFERENTES

El hook valida email comparando contra el host real del remote:

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

# Chain to local repo hooks if they exist
local_hook="$(git rev-parse --git-dir 2>/dev/null)/hooks/pre-commit"
if [[ -x "$local_hook" ]]; then
    exec "$local_hook" "$@"
fi
```

##### Escenario MISMO HOST

El hook no puede distinguir por host (ambos son github.com). Dos estrategias:

**Estrategia A — Validar por SSH alias en remote URL (si se usan aliases):**

```bash
#!/bin/bash
remote_url=$(git remote get-url origin 2>/dev/null)
user_email=$(git config user.email)

# Mismo host con aliases SSH: github.com-personal, github.com-work
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

# Chain to local repo hooks
local_hook="$(git rev-parse --git-dir 2>/dev/null)/hooks/pre-commit"
if [[ -x "$local_hook" ]]; then
    exec "$local_hook" "$@"
fi
```

**Estrategia B — Validar por directorio (fallback si no hay aliases):**

```bash
#!/bin/bash
user_email=$(git config user.email)
repo_dir=$(git rev-parse --show-toplevel 2>/dev/null)

# Validar por ubicacion del repo
if [[ "$repo_dir" == "$HOME/{SANDBOX_RELATIVO}"* ]] && [[ "$user_email" != "{EMAIL_SANDBOX}" ]]; then
    echo "COMMIT BLOCKED: repo in sandbox but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_SANDBOX}" >&2
    exit 1
fi

if [[ "$repo_dir" != "$HOME/{SANDBOX_RELATIVO}"* ]] && [[ "$user_email" != "{EMAIL_PRINCIPAL}" ]]; then
    echo "COMMIT BLOCKED: repo outside sandbox but email is '$user_email'" >&2
    echo "  Expected: {EMAIL_PRINCIPAL}" >&2
    exit 1
fi

# Chain to local repo hooks
local_hook="$(git rev-parse --git-dir 2>/dev/null)/hooks/pre-commit"
if [[ -x "$local_hook" ]]; then
    exec "$local_hook" "$@"
fi
```

Recomendar Estrategia A si el usuario configura SSH aliases. Si no, usar Estrategia B.

En macOS/Linux: `chmod +x` despues de crear el hook.
En Windows: Git for Windows ejecuta hooks con su bash integrado, no necesita permisos especiales.

---

#### Capa 4: SSH keys

##### Escenario HOSTS DIFERENTES

Cada host real tiene su propia entrada:

```
Host {HOST_PRINCIPAL}
  HostName {HOST_PRINCIPAL}
  User git
  IdentityFile {SSH_KEY_PRINCIPAL}

Host {HOST_SANDBOX}
  HostName {HOST_SANDBOX}
  User git
  IdentityFile {SSH_KEY_SANDBOX}
```

Verificacion: `ssh -T git@{HOST_PRINCIPAL}` y `ssh -T git@{HOST_SANDBOX}`

##### Escenario MISMO HOST

Se REQUIEREN aliases porque el mismo host real necesita dos llaves diferentes.
Sin aliases, SSH siempre usaria la primera llave que encuentre.

```
# Cuenta principal: {USERNAME_PRINCIPAL}
Host {HOST}-{ALIAS_PRINCIPAL}
  HostName {HOST}
  User git
  IdentityFile {SSH_KEY_PRINCIPAL}

# Cuenta sandbox: {USERNAME_SANDBOX}
Host {HOST}-{ALIAS_SANDBOX}
  HostName {HOST}
  User git
  IdentityFile {SSH_KEY_SANDBOX}
```

Ejemplo concreto:
```
# Cuenta trabajo
Host github.com-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_work

# Cuenta personal
Host github.com-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_personal
```

**IMPORTANTE — Los remotes deben usar el alias, no el host real:**

```bash
# Al clonar repos de la cuenta principal:
git clone git@{HOST}-{ALIAS_PRINCIPAL}:{USERNAME_PRINCIPAL}/repo.git

# Al clonar repos de la cuenta sandbox:
git clone git@{HOST}-{ALIAS_SANDBOX}:{USERNAME_SANDBOX}/repo.git

# Para repos existentes, actualizar el remote:
git remote set-url origin git@{HOST}-{ALIAS_SANDBOX}:{USERNAME_SANDBOX}/repo.git
```

Verificacion:
```
ssh -T git@{HOST}-{ALIAS_PRINCIPAL}
  → "Hi {USERNAME_PRINCIPAL}! You've been authenticated..."

ssh -T git@{HOST}-{ALIAS_SANDBOX}
  → "Hi {USERNAME_SANDBOX}! You've been authenticated..."
```

##### Instrucciones de generacion (ambos escenarios)

```
Para generar las llaves SSH:

  # Llave para cuenta principal
  ssh-keygen -t ed25519 -C "{EMAIL_PRINCIPAL}" -f {SSH_KEY_PRINCIPAL}

  # Llave para cuenta sandbox
  ssh-keygen -t ed25519 -C "{EMAIL_SANDBOX}" -f {SSH_KEY_SANDBOX}

Registrar cada clave publica en su cuenta:
  1. Copiar el contenido de {SSH_KEY}.pub
     macOS: cat {SSH_KEY}.pub | pbcopy
     Windows: Get-Content {SSH_KEY}.pub | Set-Clipboard
     Linux: cat {SSH_KEY}.pub | xclip -selection clipboard
  2. Ir a {HOST} > Settings > SSH and GPG keys > New SSH key
  3. Pegar la clave publica y guardar
```

---

### Paso 6: Verificacion final

Ejecutar el modo AUDIT completo para confirmar que las 4 capas estan OK.

Mostrar resumen:

```
## Setup completado

### Escenario: [Hosts diferentes / Mismo host ({HOST})]

| Capa | Accion |
|------|--------|
| 1. includeIf      | [Creada / Ya existia / Reparada] |
| 2. Shell guards   | [Creada / Ya existia / Reparada] |
| 3. Pre-commit hook| [Creada / Ya existia / Reparada] |
| 4. SSH keys       | [Instrucciones mostradas / Ya existia] |

Recarga tu shell para activar los cambios:
  macOS/Linux: source ~/.zshrc
  Windows: . $PROFILE
```

**Si escenario MISMO HOST, recordar al usuario:**
```
IMPORTANTE para mismo host ({HOST}):
- Al clonar repos, usa el alias SSH: git clone git@{HOST}-{ALIAS}:user/repo.git
- Los repos existentes necesitan actualizar su remote:
    git remote set-url origin git@{HOST}-{ALIAS}:user/repo.git
- Los tokens de gh se guardan en ~/.config/gh/tokens (permisos 600)
- NUNCA commitear tokens — verificar .gitignore global
```
