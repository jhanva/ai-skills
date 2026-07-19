---
name: secure
description: >
  Analisis de seguridad para proyectos locales. Detecta vulnerabilidades en codigo,
  secrets expuestos, dependencias inseguras, configuraciones de infra, y patrones
  de auth/crypto debiles. Dos modos: quick (solo archivos cambiados) y full (proyecto completo).
  Usar cuando: el usuario dice "security audit", "vulnerabilidades", "escanear seguridad",
  "security check", "buscar secrets", "revisar seguridad", "secure", o antes de deploy/release.
argument-hint: "[quick|full] [ruta al proyecto]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git ls-files:*)
  - Bash(find:*)
  - Bash(wc:*)
  - Bash(which:*)
  - Bash(npm audit:*)
  - Bash(pip-audit:*)
  - Bash(cargo audit:*)
---

# Secure — Analisis de seguridad

## Ley de hierro: READ-ONLY

**PROHIBIDO modificar, eliminar o crear archivos en el proyecto escaneado.**

- Nunca escribir archivos dentro del directorio target
- Nunca ejecutar codigo del proyecto (`npm start`, `python app.py`)
- Nunca instalar/actualizar paquetes en el target
- Nunca ejecutar `npm audit --fix` o equivalentes
- Python se permite UNICAMENTE para ejecutar los scripts de esta skill (`scan-secrets.py`); nunca para correr codigo del proyecto ni scripts ad-hoc
- Tu unico output son hallazgos reportados inline

## Resolver target

1. Si `$ARGUMENTS` contiene una ruta, usarla como target
2. Si `$ARGUMENTS` esta vacio, usar el directorio actual
3. Validar que existe y es un directorio

## Modos de operacion

### Modo QUICK (default)

Escanea **solo archivos con cambios sin commitear respecto a HEAD**. Ideal para usar durante desarrollo, antes de commit o PR. No usa subagentes.

```bash
# Archivos con cambios staged + unstaged respecto a HEAD
git diff --name-only HEAD
# Si no hay cambios, archivos del ultimo commit
git diff --name-only HEAD~1
```

Notas:
- Si se quiere comparar contra la branch base (todo lo de la rama actual), usar `git diff --name-only main...HEAD`
- `HEAD~1` falla en repos con un solo commit — en ese caso usar `git ls-files`

Solo aplica las verificaciones relevantes a los archivos cambiados.

### Modo FULL

Escanea **todo el proyecto**. Para auditorias periodicas o antes de release. Usa subagentes paralelos para proyectos medianos/grandes.

El modo se determina por `$ARGUMENTS[0]`:
- `quick` o sin argumento = modo quick
- `full` = modo full

---

## FASE 1: Reconocimiento (siempre, sin subagentes)

### 1.1 Detectar tech stack

Buscar archivos marcadores con Glob:

**Lenguajes:**
- `package.json` → JS/TS (leer dependencies para detectar framework)
- `requirements.txt` / `pyproject.toml` / `Pipfile` → Python
- `go.mod` → Go
- `Cargo.toml` → Rust
- `pom.xml` / `build.gradle` → Java/Kotlin

**Frameworks** (leer el manifiesto):
- JS: Express, Next.js, React, Vue, Fastify, NestJS, React Native, Expo
- Python: Django, Flask, FastAPI
- Go: Gin, Echo, Fiber

**Infra:**
- `Dockerfile` / `docker-compose.yml`
- `.github/workflows/` → GitHub Actions
- `.gitlab-ci.yml` → GitLab CI
- `*.tf` → Terraform

### 1.2 Estimar scope (solo modo full)

```bash
find TARGET -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/vendor/*' -not -path '*/__pycache__/*' -not -path '*/dist/*' -not -path '*/build/*' | wc -l
```

- **Pequeno (<1,000):** Scan completo, sin subagentes
- **Mediano (1,000-10,000):** Scan con 3 subagentes paralelos (code, infra, deps)
- **Grande (10,000+):** Scan critico (rutas API, auth, config, manifiestos, Docker, CI)

### 1.3 Cargar referencias segun stack

Leer SOLO los archivos de referencia relevantes de `.claude/skills/secure/references/` (ruta relativa a la raiz del proyecto):

`code-patterns.md` se organiza por categoria de vulnerabilidad (Injection, Auth & AuthZ, Crypto, Error Handling, Datos sensibles) mas una seccion final "Notas por lenguaje" (JavaScript/TypeScript, Python).

- **Siempre:** `secrets-patterns.md`
- **Si JS/TS:** `code-patterns.md` — categorias relevantes al stack + "Notas por lenguaje" (JavaScript/TypeScript)
- **Si Python:** `code-patterns.md` — categorias relevantes al stack + "Notas por lenguaje" (Python)
- **Si web app:** `code-patterns.md` — secciones Injection + Auth & AuthZ + Crypto
- **Si Docker/CI:** `infra-patterns.md`

### 1.4 Verificar herramientas externas (opcionales)

```bash
which semgrep trivy gitleaks 2>/dev/null
```

Usarlas si existen. Si no, analisis nativo con Grep + patterns de los archivos de referencia.

---

## FASE 2: Scan de secrets (siempre, primera prioridad)

Ejecutar el script de deteccion (ejecutar desde la raiz del proyecto; `python` puede ser `python3` o `py` segun la maquina):

```bash
python .claude/skills/secure/scripts/scan-secrets.py TARGET_DIR
```

En modo quick, pasar solo los archivos cambiados:

```bash
git diff --name-only HEAD | python .claude/skills/secure/scripts/scan-secrets.py --stdin TARGET_DIR
```

Si el script no esta disponible, usar Grep con patterns de `secrets-patterns.md`.

---

## FASE 3: Analisis de codigo

### Modo quick — inline, sin subagentes

Para cada archivo cambiado, verificar con Grep:
1. **Injection** (SQL, command, path traversal) — inputs sin sanitizar en queries/exec
2. **Auth/AuthZ** — endpoints sin middleware de auth, roles sin verificar
3. **Crypto** — algoritmos debiles (MD5, SHA1 para passwords), keys hardcodeadas
4. **Error handling** — stack traces expuestos al usuario, catch vacios
5. **Datos sensibles** — PII en logs, tokens en URLs, secrets en comentarios

### Modo full — subagentes paralelos (si proyecto mediano+)

Despachar 3 subagentes con Agent tool en un solo mensaje:

**Subagente 1: Code Security**
- Injection patterns en rutas/handlers
- Auth middleware coverage
- Crypto debil
- Error handling peligroso
- Incluir contenido de `code-patterns.md` en el prompt

**Subagente 2: Infra & Config**
- Docker: usuario root, secrets en build args, imagenes sin tag fijo
- CI/CD: secrets en logs, permisos excesivos, actions de terceros sin pin
- Incluir contenido de `infra-patterns.md` en el prompt

**Subagente 3: Dependencies**
- `npm audit` / `pip-audit` / `cargo audit`
- Lockfile integrity
- Dependencias desactualizadas con CVEs conocidos

---

## FASE 4: Reportar hallazgos

Output inline con formato navegable. NO generar archivo de reporte.

```markdown
## Hallazgos de seguridad

### CRITICO (arreglar antes de deploy)
- `src/api/users.ts:45` — SQL injection: input de usuario concatenado directamente en query
  CWE-89 | OWASP A03:2021
  Fix: usar parameterized queries

### ALTO
- `.env.production:3` — API key de Stripe expuesta en repo
  CWE-798 | OWASP A07:2021
  Fix: mover a variables de entorno del hosting, agregar a .gitignore

### MEDIO
- `Dockerfile:1` — Imagen base sin tag fijo (`node:latest`)
  CWE-1395 | OWASP A06:2021
  Fix: usar tag especifico (`node:20-alpine`)

### BAJO
- `src/utils/logger.ts:12` — Email de usuario en logs de debug
  CWE-532 | OWASP A09:2021
  Fix: redactar PII antes de loggear

### Resumen
| Severidad | Cantidad |
|---|---|
| Critico | N |
| Alto | N |
| Medio | N |
| Bajo | N |

Modo: [quick|full] | Stack: [detectado] | Archivos escaneados: N
```

Cada hallazgo DEBE tener:
- `archivo:linea` — referencia navegable
- CWE ID — clasificacion de debilidad
- Categoria OWASP Top 10 2021
- Fix concreto con ejemplo de codigo cuando aplique

Si no hay hallazgos: "Scan completo. No se encontraron vulnerabilidades en [N archivos escaneados]."

Argumento recibido: $ARGUMENTS
