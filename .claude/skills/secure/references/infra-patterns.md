# Patrones de seguridad en infraestructura

## Docker (CWE-250, CWE-1395)

### Grep patterns
```
# Secrets en build args
(?i)ARG.*(password|secret|key|token)
(?i)ENV.*(password|secret|key|token)\s*=

# Imagen sin tag fijo
(?i)^FROM\s+\w+:latest
(?i)^FROM\s+\w+\s*$   # Sin tag = latest implicito

# COPY de archivos sensibles
(?i)COPY.*\.(env|pem|key|crt|p12|jks)

# Instalacion sin version fija
(?i)RUN.*pip install\s+(?!.*==)
(?i)RUN.*npm install\s+(?!.*@\d)
```

### Container corriendo como root (CWE-250)

No hay regex de una linea confiable para esto. Verificar en dos pasos:

1. Grep de `^USER ` en el Dockerfile (case-insensitive)
2. Si no aparece ningun `USER` despues del ultimo `FROM` (el stage final), flag: "container corre como root"

Nota: un `USER` en un stage intermedio (builder) no cuenta — solo importa el stage final.

**Buenas practicas:**
- Usar imagenes slim/alpine con tag de version (`node:20-alpine`)
- Multi-stage builds para no incluir devDependencies
- `USER node` (o non-root) despues del ultimo FROM
- `.dockerignore` con `.env`, `.git`, `node_modules`
- No COPY `.env` al container — usar variables de entorno del runtime
- Fijar versiones de dependencias del sistema (`apt-get install package=version`)

### docker-compose

```
# Grep patterns
(?i)privileged:\s*true
(?i)network_mode:\s*host
(?i)environment:[\s\S]*?(PASSWORD|SECRET|KEY|TOKEN)\s*[:=]
# El pattern de environment usa [\s\S]*? — requiere multiline: true en el tool Grep de Claude Code
# Secrets en environment deberian usar secrets: o .env file referenciado
```

## CI/CD (CWE-798, CWE-200)

### GitHub Actions

```
# Grep patterns en .github/workflows/*.yml

# Secrets expuestos en logs
(?i)echo.*\$\{\{.*secrets\.
(?i)run:.*\$\{\{.*secrets\.   # Si el secret va en un run: puede imprimirse

# Actions de terceros sin SHA pin — flag de refs MUTABLES (branch o tag)
uses:\s*\S+@(main|master|v?[0-9][\w.]*)\s*$
# Un SHA de commit completo (40 caracteres hex) es lo pineado correcto;
# branches (main/master) y tags (v4, 4.1.2) son mutables y pueden ser reapuntados.
# BIEN (no matchea): uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29
# MAL (matchea):     uses: actions/checkout@v4

# Permisos excesivos
(?i)permissions:\s*write-all
(?i)permissions:[\s\S]*?contents:\s*write   # Solo si necesita push (usa [\s\S]*? — requiere multiline: true en el tool Grep)

# Script injection via inputs
(?i)\$\{\{\s*github\.event\.(issue|pull_request|comment)\.
# Los inputs de PR/issue son controlados por el usuario — injection risk
```

### GitLab CI

```
# Grep patterns en .gitlab-ci.yml
(?i)variables:[\s\S]*?(PASSWORD|SECRET|KEY|TOKEN)\s*:
# Usa [\s\S]*? — requiere multiline: true en el tool Grep de Claude Code
# Variables sensibles deben ir en CI/CD Variables (protected/masked), no en el yml
```

## Supply Chain (CWE-1395)

### Dependencias

**Verificaciones automaticas:**
- `npm audit` — vulnerabilidades conocidas en deps de JS
- `pip-audit` — vulnerabilidades en deps de Python
- `cargo audit` — vulnerabilidades en deps de Rust

**Verificaciones manuales:**
```
# Buscar dependencias sin lockfile
# Si existe package.json pero no package-lock.json / yarn.lock / pnpm-lock.yaml = riesgo

# Buscar scripts post-install sospechosos en package.json
(?i)"(preinstall|postinstall|preuninstall)":\s*"

# Buscar dependencias con typosquatting potencial
# Comparar nombres de paquetes contra los top 1000 de npm/pypi
```

### Lockfile integrity
- Lockfile debe existir y estar commiteado
- `npm ci` (no `npm install`) en CI para respetar el lockfile
- Verificar que lockfile y manifiesto estan sincronizados
