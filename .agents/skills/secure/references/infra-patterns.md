# Patrones de seguridad en infraestructura

## Docker (CWE-250, CWE-1395)

### Grep patterns
```
# Usuario root (default si no se especifica USER)
(?i)^FROM.*(?!.*AS\s+builder)   # Si no hay USER despues del FROM final, corre como root

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
# Secrets en environment deberian usar secrets: o .env file referenciado
```

## CI/CD (CWE-798, CWE-200)

### GitHub Actions

```
# Grep patterns en .github/workflows/*.yml

# Secrets expuestos en logs
(?i)echo.*\$\{\{.*secrets\.
(?i)run:.*\$\{\{.*secrets\.   # Si el secret va en un run: puede imprimirse

# Actions de terceros sin SHA pin
(?i)uses:\s+[^@]+@(?!main$|master$)[a-z]   # Usar SHA, no tags
# BIEN: uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29
# MAL:  uses: actions/checkout@v4

# Permisos excesivos
(?i)permissions:\s*write-all
(?i)permissions:[\s\S]*?contents:\s*write   # Solo si necesita push

# Script injection via inputs
(?i)\$\{\{\s*github\.event\.(issue|pull_request|comment)\.
# Los inputs de PR/issue son controlados por el usuario — injection risk
```

### GitLab CI

```
# Grep patterns en .gitlab-ci.yml
(?i)variables:[\s\S]*?(PASSWORD|SECRET|KEY|TOKEN)\s*:
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
