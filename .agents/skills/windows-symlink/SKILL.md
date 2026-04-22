---
name: windows-symlink
description: "Audita, habilita y repara soporte de symlinks en Windows para repos Git y workflows de Codex. Úsala cuando el usuario quiera montar symlinks en Windows, validar Developer Mode o permisos de administrador, revisar `core.symlinks`, probar creación real de symlinks, o recuperar un checkout donde Git dejó links como archivos planos."
---

# Windows Symlink — Soporte de symlinks en Windows

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$windows-symlink`.
- Usa PowerShell y `git` para auditar el entorno; lee solo los archivos de config o repo que sean necesarios.
- Modos: `audit` por defecto, `setup` para habilitar soporte, `repair` para recuperar un checkout roto.
- `audit` es read-only.
- `setup` puede modificar config global de Git y, si el usuario lo autoriza y la sesion es elevada, settings del sistema fuera del workspace. Explica siempre que vas a tocar antes de hacerlo.
- `repair` puede requerir re-clonar o re-checkout del repo. Si el repo no esta limpio, detente antes de proponer acciones destructivas.

## Objetivo

Conseguir que los symlinks de archivo funcionen de forma real en Windows y que Git no los deje convertidos en archivos de texto plano dentro del checkout.

## Carga just-in-time

- Lee `references/windows-requirements.md` cuando necesites validar prerequisitos, permisos, filesystem o alternativas como junctions y hard links.
- Lee `references/git-recovery.md` cuando el repo ya este clonado y los symlinks salgan como archivos planos o cuando debas escoger entre fresh clone e in-place repair.

## Flujo

1. Determinar modo.
2. Confirmar que estas en Windows.
3. Ejecutar la auditoria base.
4. Si el modo es `setup`, habilitar lo faltante y volver a auditar.
5. Si el modo es `repair`, validar el estado del repo y elegir la estrategia de recuperacion mas segura.

## Determinar modo

- Si el prompt contiene `setup`, usa modo `setup`.
- Si el prompt contiene `repair`, `fix` o `recover`, usa modo `repair`.
- Si no, usa modo `audit`.

## Paso 1: Auditoria base

Ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/windows-symlink/scripts/audit-windows-symlink.ps1 -RepoPath .
```

Si el usuario paso otra ruta, usala en `-RepoPath`.

La auditoria debe responder como minimo:

- Windows detectado o no
- PowerShell y Git disponibles o no
- si el volumen parece NTFS
- si la sesion es admin
- si Developer Mode parece activo
- valor global de `git config --global core.symlinks`
- valor efectivo de `core.symlinks` dentro de `-RepoPath` y si existe override local
- si se pudo crear un symlink real en una carpeta temporal
- si el repo tiene entradas `120000` en Git y si hoy existen como symlink real o como archivo plano

## Paso 2: Setup

Antes de modificar nada, explica el plan. El setup ideal incluye:

1. asegurar `git config --global core.symlinks true`
2. si `-RepoPath` es un repo Git y tiene override local en `false`, corregir `git -C <repo> config --local core.symlinks true`
3. si el sistema no puede crear symlinks y el usuario autoriza cambios del OS:
   - intentar habilitar Developer Mode desde PowerShell elevada
   - si no se puede, dar la ruta exacta en Settings para activarlo manualmente
4. volver a correr la auditoria

Usa:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/windows-symlink/scripts/setup-windows-symlink.ps1 -RepoPath .
```

Si el usuario autorizo cambios del sistema y la shell esta elevada, agrega `-TryEnableDeveloperMode`.

## Paso 3: Repair

Si el repo ya esta mal chequeado:

1. leer `references/git-recovery.md`
2. revisar `git status --short`
3. si hay cambios locales, no intentes repair destructivo
4. si el repo esta limpio, preferir fresh clone despues de habilitar symlinks
5. solo si el usuario pide repair in-place y el repo esta limpio, proponer un re-checkout o `git reset --hard HEAD`

## Reglas importantes

- No confundas symlink con junction o hard link: para entradas Git `120000`, no son reemplazos equivalentes.
- Si el filesystem no soporta bien symlinks o la politica del equipo los bloquea, dilo explicitamente y usa el fallback documentado en `references/git-recovery.md`.
- Si la auditoria ya muestra `can_create_symlink = true` y el valor efectivo de `core.symlinks` en el repo es `true`, pero el repo sigue roto, el problema casi siempre es el checkout previo.

## Output esperado

```markdown
## Windows symlink status

### Estado
- OS:
- Filesystem:
- Admin:
- Developer Mode:
- Git core.symlinks global:
- Git core.symlinks efectivo:
- Override local en repo:
- Temp symlink test:

### Repo
- Entradas symlink en Git:
- Entradas rotas en checkout:
- Ejemplos:

### Siguiente paso recomendado
- audit limpio / setup / fresh clone / repair in-place
```

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompane a la invocacion de la skill.
