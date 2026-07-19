---
name: browser-control
description: >
  Control directo del browser via CDP (Chrome DevTools Protocol). Conecta al
  Chrome real del usuario y ejecuta navegacion, screenshots, clicks, input,
  evaluacion JS y manejo de tabs. Usala cuando el usuario pida busqueda web,
  buscar en internet, investigar paginas web, controlar, inspeccionar o
  automatizar un navegador real desde Codex.
---

# Browser Control - CDP directo

Control del browser real del usuario via Chrome DevTools Protocol. Un WebSocket a Chrome, nada entre medio.

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$browser-control`.
- No modifiques la capa `.claude/`; usa esta version nativa en `.agents/skills/browser-control`.
- Usa lecturas puntuales con `rg`, `rg --files`, `find` y `sed -n` cuando necesites inspeccionar archivos.
- Ejecuta comandos shell puntuales con `exec_command`; si necesitas editar archivos del repo, usa `apply_patch`.
- Verifica acciones del browser con `screenshot()` o una lectura de estado despues de navegar, hacer click o escribir.

## Primer movimiento

1. Si es la primera vez, leer `references/connection-guide.md` y configurar la conexion.
2. Ejecutar el test de conexion desde la raiz del repo. Usa el launcher de
   Python disponible (`python`, `python3` o `py -3`):

```bash
python .agents/skills/browser-control/references/cdp_helpers.py
```

3. Si falla, seguir la guia de troubleshooting en `references/connection-guide.md`.

## Patron de uso

Ejecutar scripts Python inline y pasar la ruta de helpers como argumento, sin
interpolarla dentro del codigo. En PowerShell:

```powershell
@'
import sys
sys.path.insert(0, sys.argv[1])
from cdp_helpers import *

connect()
new_tab("https://example.com")
wait_for_load()
info = page_info()
print(f"{info['title']} - {info['url']}")
path = screenshot()
print(f"Screenshot: {path}")
close()
'@ | python - ".agents/skills/browser-control/references"
```

En bash/zsh usa el equivalente `python - ".agents/.../references" <<'PY'`.
Mantener `PY` entre comillas evita expansion del shell dentro del codigo.

## API de helpers

### Conexion

| Funcion | Descripcion |
|---|---|
| `connect(ws_url=None)` | Conectar a Chrome. Auto-descubre si no se pasa URL |
| `close()` | Cerrar la conexion WebSocket |
| `cdp(method, **params)` | Enviar comando CDP raw. Retorna el resultado |

### Navegacion

| Funcion | Descripcion |
|---|---|
| `goto(url)` | Navegar a una URL en el tab actual |
| `page_info()` | `{url, title, w, h, sx, sy, pw, ph}` - viewport + scroll + dimensiones |
| `wait_for_load(timeout=15)` | Esperar `readyState == 'complete'` |
| `wait_for_element(selector, timeout=10, visible=False)` | Esperar a que un selector CSS exista en el DOM |
| `wait_for_idle(timeout=10)` | Esperar a que no haya requests de red pendientes |

### Input

| Funcion | Descripcion |
|---|---|
| `click_at_xy(x, y, button="left", clicks=1)` | Click en coordenadas CSS. Nivel compositor: atraviesa iframes y shadow DOM |
| `type_text(text)` | Insertar texto en el foco actual. Rapido pero sin event listeners |
| `fill_input(selector, text, clear_first=True)` | Llenar input con key events reales (React, Vue, etc.) |
| `press_key(key, modifiers=0)` | Tecla individual. Modifiers: 1=Alt, 2=Ctrl, 4=Meta, 8=Shift |
| `scroll(x, y, dy=-300, dx=0)` | Scroll en las coordenadas dadas. dy negativo = hacia abajo |

### Visual

| Funcion | Descripcion |
|---|---|
| `screenshot(path=None, full=False)` | Capturar PNG. Sin path usa `cdp_screenshot.png` en el directorio temporal del sistema. `full=True` captura pagina completa |

### Tabs

| Funcion | Descripcion |
|---|---|
| `list_tabs(include_internal=False)` | Listar tabs abiertas `[{targetId, title, url}]` |
| `current_tab()` | Info del tab actual |
| `new_tab(url="about:blank")` | Abrir tab nuevo y cambiar a el |
| `switch_tab(target)` | Cambiar a tab por targetId (string o dict) |
| `ensure_real_tab()` | Ir a un tab real si estamos en uno interno |

### DOM / JS

| Funcion | Descripcion |
|---|---|
| `js(expression)` | Evaluar JavaScript. Retorna el valor |
| `upload_file(selector, filepath)` | Subir archivo a un `<input type=file>` |
| `handle_dialog(accept=True)` | Aceptar o cancelar dialog JS (alert/confirm/prompt) |

### Utilidad

| Funcion | Descripcion |
|---|---|
| `wait(seconds=1.0)` | Sleep. Preferir `wait_for_load()` o `wait_for_element()` |

## Que funciona

- **Screenshots first**: `screenshot()` para entender la pagina, encontrar targets visibles, decidir si hacer click o usar selectores.
- **Clicking**: `screenshot()` -> localizar target en la imagen -> `click_at_xy(x, y)` -> `screenshot()` para verificar. Preferir sobre selectores DOM.
- **Framework inputs**: `fill_input(selector, text)` cuando `type_text()` no dispara validacion de React/Vue/Angular.
- **Bulk HTTP sin browser**: `urllib.request.urlopen()` con `ThreadPoolExecutor` para scraping de paginas estaticas.
- **Auth wall**: si la pagina redirige a login, detenerse y preguntar al usuario. No escribir credenciales leidas de screenshots.

## Gotchas

- **Omnibox popups** son targets falsos tipo `page`. Filtrar URLs que empiezan con `chrome://omnibox-popup`.
- **DevicePixelRatio**: screenshots son en device pixels. En displays 2x, dividir coordenadas de la imagen por `js("window.devicePixelRatio")` antes de pasarlas a `click_at_xy()`.
- **Primer tab**: usar `new_tab(url)`, no `goto(url)`; `goto` navega en el tab activo del usuario y sobreescribe su trabajo.
- **Dialogs bloquean JS**: si `page_info()` falla despues de una accion, puede haber un dialog pendiente. Usar `handle_dialog()`.
- **Tab order CDP != visual**: el orden de `list_tabs()` no coincide con la barra de tabs visible. Si importa el orden visual, usar AppleScript en macOS o UI Automation/PowerShell en Windows.
- **Stale sessions**: si un tab se cierra externamente, las llamadas CDP fallan. Reconectar con `ensure_real_tab()`.
- **Verificar despues de actuar**: siempre `screenshot()` despues de clicks o navegacion para confirmar que la accion funciono.

## Reglas

- Conectar al Chrome que el usuario ya tiene abierto. No lanzar un browser nuevo salvo que el usuario lo pida.
- `cdp()` para cualquier cosa que los helpers no cubran. La referencia completa del protocolo esta en `chromedevtools.github.io/devtools-protocol`.
- Mantener scripts cortos y autocontenidos. Si algo se vuelve complejo, escribir un helper reutilizable dentro de esta skill.
- No agregar layers de abstraccion como retry framework, session manager o config system. Si falla, diagnosticar.

## Carga just-in-time

- `references/cdp_helpers.py` - modulo Python con todos los helpers
- `references/connection-guide.md` - setup y troubleshooting de conexion al browser
- `references/interaction-patterns.md` - patrones para mecanicas web complejas (dialogs, iframes, dropdowns, uploads)

## Variables de entorno

| Variable | Uso |
|---|---|
| `CDP_WS_URL` | WebSocket URL directa (override de auto-discovery) |
| `CDP_URL` | HTTP DevTools endpoint, por ejemplo `http://127.0.0.1:9222`. Se resuelve a WS via `/json/version` |
