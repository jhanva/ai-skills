# Patrones de deteccion de secrets

Regex patterns para detectar secrets expuestos en codigo fuente. Cada pattern incluye el tipo de secret, la regex, y la tasa de falsos positivos esperada.

## Alta confianza (casi nunca falso positivo)

| Tipo | Regex | Ejemplo |
|---|---|---|
| AWS Access Key | `AKIA[0-9A-Z]{16}` | AKIAIOSFODNN7EXAMPLE |
| AWS Secret Key | `(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}` | |
| GitHub Token (classic) | `ghp_[A-Za-z0-9]{36}` | ghp_xxxxxxxxxxxx |
| GitHub Token (fine-grained) | `github_pat_[A-Za-z0-9_]{82}` | |
| GitHub OAuth | `gho_[A-Za-z0-9]{36}` | |
| GitLab Token | `glpat-[A-Za-z0-9\-]{20}` | |
| Slack Bot Token | `xoxb-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}` | |
| Slack Webhook | `https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}` | |
| Stripe Secret Key | `sk_live_[A-Za-z0-9]{24,}` | |
| Stripe Publishable | `pk_live_[A-Za-z0-9]{24,}` | |
| Twilio API Key | `SK[0-9a-fA-F]{32}` | |
| SendGrid API Key | `SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43}` | |
| Google API Key | `AIza[0-9A-Za-z\-_]{35}` | |
| Firebase (no prefix) | `(?i)(firebase|firebaseio).*['\"][A-Za-z0-9\-_]{30,}['\"]` | |
| Heroku API Key | `(?i)heroku.*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` | |
| npm Token | `npm_[A-Za-z0-9]{36}` | |
| PyPI Token | `pypi-[A-Za-z0-9]{50,}` | |

## Confianza media (verificar contexto)

| Tipo | Regex | Notas |
|---|---|---|
| Private key header | `-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----` | Puede ser test fixture |
| Generic password assignment | `(?i)(password\|passwd\|pwd)\s*[:=]\s*['"][^'"]{8,}['"]` | Excluir archivos de test y .example |
| Generic secret assignment | `(?i)(secret\|token\|api_key\|apikey\|access_key)\s*[:=]\s*['"][^'"]{8,}['"]` | Excluir .example y docs |
| Connection string con password | `(?i)(mongodb\|postgres\|mysql\|redis)://[^:]+:[^@]+@` | Puede ser localhost de dev |
| JWT hardcodeado | `eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+` | Puede ser test fixture |
| Bearer token hardcodeado | `(?i)bearer\s+[A-Za-z0-9\-_.~+/]{20,}` | |

## Archivos a escanear con prioridad

1. `.env`, `.env.*` (excepto `.env.example`)
2. `*.config.js`, `*.config.ts`, `config/*.{json,yaml,yml}`
3. `docker-compose*.yml` (environment sections)
4. `.github/workflows/*.yml` (env y secrets)
5. `src/**/*.{js,ts,py,go,rb,java}` (imports y asignaciones)
6. `*.tf`, `*.tfvars` (variables de Terraform)

## Archivos a IGNORAR

- `*.test.*`, `*_test.*`, `*_spec.*` (test fixtures con tokens falsos)
- `*.example`, `*.sample`, `*.template`
- `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`
- `*.lock`, `*.min.js`, `*.min.css`
- Archivos binarios e imagenes
