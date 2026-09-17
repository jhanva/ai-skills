# Guia de conexion al browser

## Prerequisitos

- Chrome, Edge, Brave u otro browser basado en Chromium
- Python 3.11+
- `websockets` (instalar con `pip install websockets`)

## Formas de conectar

### Way 1: chrome://inspect checkbox (perfil real)

Usa tu browser con sesiones activas, cookies, extensiones. Ideal para tareas en tu browser real.

1. Abrir Chrome
2. Navegar a `chrome://inspect/#remote-debugging`
3. Marcar "Allow remote debugging for this browser instance"
4. En Chrome 144+, aceptar el popup "Allow remote debugging?" cuando aparezca

La casilla es persistente por perfil. Solo se marca una vez.

En macOS se puede abrir la pagina automaticamente:

```bash
osascript -e 'tell application "Google Chrome" to activate' \
          -e 'tell application "Google Chrome" to open location "chrome://inspect/#remote-debugging"'
```

### Way 2: flag de linea de comandos (perfil aislado)

Para automatizacion sin interrupcion. No usa tu perfil real — sesiones limpias.

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-automation

# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-automation

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir=%TEMP%\chrome-automation
```

Configurar la variable de entorno para que los helpers encuentren el endpoint:

```bash
export CDP_URL=http://127.0.0.1:9222
```

**Restriccion en Chrome 136+:** el flag `--remote-debugging-port` se ignora silenciosamente si `--user-data-dir` apunta al directorio default del perfil. Siempre usar una ruta diferente.

**Cookies no se transfieren:** copiar el directorio default a otro path no preserva las cookies (estan cifradas con una key vinculada a la ruta original).

## Descubrimiento automatico

Los helpers buscan Chrome en este orden:

1. `CDP_WS_URL` — URL WebSocket directa (si esta definida)
2. `CDP_URL` — endpoint HTTP DevTools, se resuelve via `/json/version`
3. **DevToolsActivePort** — archivo que Chrome escribe en el directorio del perfil con el puerto y path del WebSocket. Se busca en las ubicaciones conocidas:

| OS | Ubicaciones |
|---|---|
| macOS | `~/Library/Application Support/Google/Chrome/`, Chrome Canary, Edge, Brave |
| Linux | `~/.config/google-chrome/`, chromium, microsoft-edge |
| Windows | `%LOCALAPPDATA%\Google\Chrome\User Data\`, Edge |

4. **Puertos conocidos** — prueba 9222 y 9223 via `/json/version`

## Test de conexion

```bash
python path/to/cdp_helpers.py   # o python3/py segun la maquina
```

Output exitoso:
```
Chrome found: ws://127.0.0.1:XXXXX/devtools/browser/UUID
Connected to: Tab Title — https://url
Connection test passed.
```

## Troubleshooting

### "Chrome not found"

**Causa:** no hay Chrome con debugging habilitado.

- Way 1: verificar que la casilla en `chrome://inspect/#remote-debugging` esta marcada
- Way 2: verificar que Chrome fue lanzado con `--remote-debugging-port` y un `--user-data-dir` no-default
- Verificar que Chrome esta corriendo: `ps aux | grep -i chrome` (macOS/Linux) o `tasklist | findstr chrome` (Windows)

### "CDP WS handshake failed"

**Causa:** Chrome esta corriendo pero rechazo la conexion.

- Chrome 144+: click "Allow" en el popup de remote debugging que aparece en el browser
- Verificar que no hay otro proceso usando el puerto 9222: `lsof -i :9222` (macOS/Linux)
- Si se uso Way 2, confirmar que el `--user-data-dir` no es el default

### "DevToolsActivePort not found"

**Causa:** Chrome esta corriendo pero el archivo de puerto no existe en ninguna ubicacion conocida.

- Puede ser un browser no-Chromium (Firefox, Safari no soportan CDP)
- En Linux con Snap: Snap confina el filesystem y DevToolsActivePort no esta accesible. Instalar Chrome nativo en vez del Snap
- Verificar manualmente: `find ~/Library -name DevToolsActivePort 2>/dev/null` (macOS)

### Funciona pero los clicks no hacen nada

- `screenshot()` para verificar que se esta viendo la pagina correcta
- Verificar DevicePixelRatio: `js("window.devicePixelRatio")`. En displays 2x las coordenadas del screenshot se dividen por el DPR
- Puede haber un overlay/modal/dialog bloqueando. Usar `handle_dialog()` o cerrar el overlay

### La sesion se vuelve stale

Si Chrome cierra un tab externamente o la conexion se interrumpe:

```python
ensure_real_tab()  # re-attach a un tab valido
```

Si eso falla:

```python
close()
connect()
```
