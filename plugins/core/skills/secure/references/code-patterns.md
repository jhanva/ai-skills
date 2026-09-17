# Patrones de seguridad en codigo

## Injection (CWE-89, CWE-78, CWE-22)

### SQL Injection
**Buscar:** concatenacion de strings en queries SQL

```
# Grep patterns
(?i)(query|execute|raw|sql)\s*\(.*\$\{
(?i)(query|execute|raw|sql)\s*\(.*\+\s*(req|request|params|body|query|input|args)
(?i)WHERE.*=\s*['"]?\s*\+\s*
```

**Vulnerable (JS):**
```javascript
db.query(`SELECT * FROM users WHERE id = ${req.params.id}`)
```

**Seguro:**
```javascript
db.query('SELECT * FROM users WHERE id = $1', [req.params.id])
```

### Command Injection
**Buscar:** input de usuario en exec/spawn/system

```
# Grep patterns
(?i)(exec|spawn|system|popen|subprocess)\s*\(.*\$\{
(?i)(exec|spawn|system|popen|subprocess)\s*\(.*\+\s*(req|request|params|body|input)
child_process.*\$\{
```

**Vulnerable (JS):**
```javascript
exec(`convert ${req.body.filename} output.png`)
```

**Seguro:**
```javascript
execFile('convert', [sanitizedFilename, 'output.png'])
```

### Path Traversal
**Buscar:** input de usuario en rutas de archivo

```
# Grep patterns
(?i)(readFile|writeFile|readdir|unlink|open)\s*\(.*\$\{
(?i)path\.(join|resolve)\s*\(.*req\.(params|query|body)
(?i)\.\./
```

**Vulnerable (JS):**
```javascript
fs.readFile(path.join(uploadDir, req.params.filename))
```

**Seguro:**
```javascript
const safeName = path.basename(req.params.filename) // strip ../
const fullPath = path.join(uploadDir, safeName)
if (!fullPath.startsWith(uploadDir)) throw new Error('Invalid path')
```

## Auth & AuthZ (CWE-862, CWE-863, CWE-306)

### Endpoints sin autenticacion
**Buscar:** handlers de rutas sin middleware de auth

```
# Grep patterns
(?i)(app|router)\.(get|post|put|patch|delete)\s*\(\s*['"]/(admin|api|user|dashboard|settings)
# Y verificar que NO tienen middleware de auth antes del handler
```

### Broken access control
**Buscar:** acceso a recursos sin verificar ownership

```
# Patron peligroso: buscar por ID sin filtrar por usuario
(?i)findById|findOne.*\{.*id.*req\.params
# Sin un WHERE user_id = currentUser.id
```

### Password handling
**Buscar:** passwords en plaintext, hashing debil

```
# Grep patterns
(?i)(password|passwd)\s*===?\s*(req|body|params|input)
(?i)(md5|sha1|sha256)\s*\(.*password
# Deberian usar bcrypt, scrypt, o argon2
```

## Crypto (CWE-327, CWE-328, CWE-330)

### Algoritmos debiles
**Buscar:**
```
# Grep patterns
(?i)createHash\s*\(\s*['"]md5['"]
(?i)createHash\s*\(\s*['"]sha1['"]
(?i)DES|RC4|ECB
(?i)Math\.random\(\).*(?i)(token|secret|key|password|salt|nonce|iv)
```

MD5 y SHA1 estan rotos para integridad. Usar SHA-256+.
`Math.random()` no es criptograficamente seguro. Usar `crypto.randomBytes()`.

### Keys y IVs hardcodeados
**Buscar:**
```
(?i)(key|iv|secret|salt)\s*=\s*['"][A-Fa-f0-9]{16,}['"]
(?i)(key|iv|secret|salt)\s*=\s*Buffer\.from\s*\(['"][^'"]+['"]\)
```

## Error Handling (CWE-209, CWE-390)

### Stack traces expuestos
**Buscar:**
```
(?i)res\.(send|json|status).*err\.(stack|message)
(?i)console\.(log|error)\s*\(.*err
# En produccion, nunca exponer stack traces al usuario
```

### Catch vacios
**Buscar:**
```
catch\s*\([^)]*\)\s*\{\s*\}
except\s*:\s*pass
# Catch sin handling = bugs silenciosos
```

## Datos sensibles (CWE-532, CWE-312)

### PII en logs
**Buscar:**
```
(?i)(console\.(log|info|warn|error)|logger\.(info|warn|error|debug)).*(?i)(email|password|ssn|credit.?card|token|secret|api.?key)
```

### Tokens en URLs
**Buscar:**
```
(?i)(token|key|secret|password)=.*(?i)(window\.location|req\.url|req\.query)
# Tokens en query params se guardan en logs de servidor, historial de browser, y referrer headers
```

## Notas por lenguaje

### JavaScript / TypeScript
- `eval()`, `new Function()`, `setTimeout(string)` = code injection
- `dangerouslySetInnerHTML` sin sanitizar = XSS
- `document.write()` con input de usuario = XSS
- `innerHTML` con datos externos = XSS
- `__proto__` pollution via `Object.assign` con input sin validar

### Python
- `eval()`, `exec()`, `compile()` con input externo = code injection
- `pickle.loads()` con datos no confiables = arbitrary code execution
- `yaml.load()` sin `Loader=SafeLoader` = code injection
- `subprocess.shell=True` con input externo = command injection
- `format()` / f-strings en queries SQL = SQL injection
