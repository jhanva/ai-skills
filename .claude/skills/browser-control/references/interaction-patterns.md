# Patrones de interaccion web

Referencia para mecanicas web que requieren tratamiento especial. Cargar solo cuando la tarea involucre una de estas mecanicas.

## Dialogs (alert / confirm / prompt / beforeunload)

Los dialogs nativos congelan el hilo JS. `page_info()` y `js()` fallan mientras uno esta abierto.

### Detectar

Si `page_info()` lanza error despues de una accion, probablemente hay un dialog pendiente.

### Dismissar via CDP (preferido)

```python
handle_dialog(accept=True)   # click OK / aceptar
handle_dialog(accept=False)  # click Cancel / cancelar
```

No inyecta JS — indetectable por antibot.

### Prevenir via JS

Interceptar antes de que aparezcan. Se pierde en cada navegacion.

```python
js("""
window.__dialogs__=[];
window.alert=m=>window.__dialogs__.push(String(m));
window.confirm=m=>{window.__dialogs__.push(String(m));return true;};
window.prompt=(m,d)=>{window.__dialogs__.push(String(m));return d||'';};
""")
```

### beforeunload

Se dispara al navegar fuera de paginas con cambios sin guardar.

```python
# Opcion A: dismissar despues de navegar
goto("https://nuevo-destino.com")
try:
    handle_dialog(accept=True)
except Exception:
    pass

# Opcion B: prevenir antes de navegar
js("window.onbeforeunload=null")
goto("https://nuevo-destino.com")
```

## Iframes

### Same-origin

Acceder al DOM del iframe via JS:

```python
js("""
const frame = document.querySelector('iframe').contentDocument;
frame.querySelector('.btn').click();
""")
```

### Cross-origin

No se puede acceder al DOM desde JS. Dos opciones:

1. **Clicks por coordenadas** (preferido): `click_at_xy()` atraviesa iframes a nivel compositor.
2. **Attachear al target del iframe**: CDP expone iframes como targets separados.

```python
targets = cdp("Target.getTargets")["targetInfos"]
iframe = next(t for t in targets if t["type"] == "iframe" and "dominio.com" in t.get("url", ""))
resp = cdp("Target.attachToTarget", targetId=iframe["targetId"], flatten=True)
# Usar resp["sessionId"] para enviar comandos al iframe
```

## Shadow DOM

`querySelector()` no penetra shadow roots. Dos opciones:

1. **Clicks por coordenadas**: siempre funcionan, ignoran la estructura DOM.
2. **Traversar shadow roots**:

```python
js("""
const host = document.querySelector('my-component');
const shadow = host.shadowRoot;
const btn = shadow.querySelector('.submit-btn');
btn.click();
""")
```

Para shadows profundos, preferir coordenadas sobre traversal recursivo.

## Dropdowns

### `<select>` nativo

```python
js("""
const sel = document.querySelector('select#country');
sel.value = 'CO';
sel.dispatchEvent(new Event('change', {bubbles: true}));
""")
```

### Custom dropdown (overlay)

1. Click para abrir el dropdown
2. `wait(0.3)` o `wait_for_element('.dropdown-option')` para que renderice
3. `screenshot()` para ver las opciones
4. `click_at_xy()` en la opcion deseada

Las coordenadas de las opciones cambian despues de abrir — siempre hacer screenshot post-apertura.

### Searchable combobox

```python
click_at_xy(x_input, y_input)
type_text("colombia")
wait_for_element('[data-option="CO"]')
# screenshot para verificar opciones visibles
click_at_xy(x_opcion, y_opcion)
```

## Uploads

### Input file standard

```python
upload_file("input[type=file]", "/ruta/absoluta/al/archivo.pdf")
```

No requiere interaccion visual. Funciona con inputs ocultos (display:none).

### Drag-and-drop zones

Si el sitio solo acepta drag-and-drop, buscar el input file oculto que suele existir debajo:

```python
# Buscar input oculto
has_input = js("!!document.querySelector('input[type=file]')")
if has_input:
    upload_file("input[type=file]", "/ruta/archivo.pdf")
```

Si no hay input oculto, disparar eventos drag programaticamente:

```python
js("""
const dt = new DataTransfer();
const dropzone = document.querySelector('.drop-zone');
dropzone.dispatchEvent(new DragEvent('drop', {dataTransfer: dt, bubbles: true}));
""")
```

## Screenshots y coordenadas

### DevicePixelRatio

En displays Retina (2x), el screenshot tiene el doble de pixeles que la ventana CSS.

```python
dpr = js("window.devicePixelRatio") or 1
# Si mides un target en el screenshot en pixel (px, py):
css_x = px / dpr
css_y = py / dpr
click_at_xy(css_x, css_y)
```

### Full page vs viewport

- `screenshot()` — viewport visible. Rapido, suficiente para la mayoria de tareas.
- `screenshot(full=True)` — pagina completa. Lento en paginas largas. Util para capturar contenido below-the-fold.

## Scrolling

### Pagina

```python
scroll(400, 400, dy=-500)      # scroll down 500px
scroll(400, 400, dy=500)       # scroll up 500px
```

### Container con overflow

El scroll se despacha en las coordenadas dadas. Si hay un container scrolleable debajo de esas coordenadas, ese container recibe el scroll en vez de la pagina.

### Scroll al fondo

```python
js("window.scrollTo(0, document.documentElement.scrollHeight)")
```

### Scroll a elemento

```python
js("document.querySelector('.target').scrollIntoView({behavior:'smooth'})")
```

## Network idle

`wait_for_idle()` usa una heuristica basada en `performance.getEntriesByType('resource')`. Para SPAs que cargan datos via fetch despues del load:

```python
wait_for_load()                    # esperar el load inicial
wait_for_element('.data-loaded')   # esperar al indicador del framework
```

Es mas confiable que esperar idle de red para aplicaciones React/Vue/Angular que mutan el DOM asincrona mente.
