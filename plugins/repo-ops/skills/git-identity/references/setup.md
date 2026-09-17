# Git Identity Setup Reference

Lee este archivo solo cuando el modo sea `setup`.

## Flujo de setup

1. Auditar primero
2. Recopilar datos faltantes
3. Configurar solo capas faltantes o rotas
4. Re-auditar al final

## Capas a configurar

### 1. includeIf
- Git global principal
- Archivo sandbox separado
- Validar formato de ruta con `git rev-parse --show-toplevel`

### 2. Shell guards o auto-switch
- Hosts distintos: wrappers que bloquean CLI fuera del directorio correcto
- Mismo host: auto-switch de `GH_TOKEN` por directorio y aliases SSH

### 3. Pre-commit hook global
- Validar email esperado segun remote o segun directorio
- Reejecutar hook local si existe

### 4. SSH keys
- No generar claves sin confirmacion
- Para mismo host, usar aliases SSH distintos
- Verificar con `ssh -T`

## Verificacion final

- Re-correr `audit`
- Reportar estado por capa
- Sugerir recargar shell

## Reglas de seguridad

- No reconfigurar a ciegas
- No escribir fuera del repo sin resumir archivos a tocar y pedir confirmacion
- No commitear tokens ni secretos
