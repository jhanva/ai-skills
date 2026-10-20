# Spec: Clone pack — reconstruir apps Android y de PC para uso propio

Fecha: 2026-10-20
Estado: aprobada en brainstorm, pendiente de /plan

## 1. Problema y contexto

Quiero reconstruir apps existentes (Android y escritorio Windows) como version
propia, para uso personal o de mi equipo. Hoy el repo tiene el flujo general
(/plan, /execute, /tdd, /verify) pero nada que:

- desarme una app instalada en pantallas, flujos, features y modelo de datos
  de forma sistematica y con evidencia,
- elija el stack del clon segun la app objetivo,
- guie la construccion pantalla por pantalla contra el original,
- mida objetivamente cuanto le falta al clon para igualar al original.

### Decisiones tomadas en brainstorm

| tema | decision |
|---|---|
| objetivo | reconstruir para uso propio. Sin rebrand, sin tiendas, sin analisis de mercado |
| plataformas objetivo | apps Android y apps de escritorio Windows |
| stack del clon | depende de la app; `/clone-arch` lo elige con una matriz y lo justifica |
| captura en recon | semi-automatica: el usuario navega, la skill captura screenshot + arbol de UI |
| medicion de paridad | score de features + diff de arbol de UI por pantalla |
| runtime | plugin `clone` (Claude Code y Codex leen `plugins/clone/skills/`) |
| estructura | enfoque C: pack de cuatro skills con ciclo de construccion propio |

## 2. Enfoque elegido y justificacion

Pack de cuatro skills (`/clone-recon`, `/clone-arch`, `/clone-build`,
`/clone-diff`) que comparten una carpeta de trabajo `clone/` en el proyecto
del clon y un formato de arbol de UI neutral a la plataforma.

Se eligio sobre "dos skills" y "una skill con modos" porque el ciclo de
construccion de un clon tiene una definicion de terminado propia (cada
pantalla cierra con captura del clon y diff contra el original) que `/execute`
no conoce. `/clone-build` reutiliza `/tdd` para la logica, no lo reemplaza.

La pieza tecnica central es el arbol normalizado: un mismo JSON para Android
(uiautomator), Windows (UI Automation) y clones web en WebView2/navegador
(tambien expuestos por UI Automation). Gracias a eso el diff compara un
original Android con un clon de escritorio.

## 3. Diseno detallado

### 3.1 Archivos del pack

```
plugins/clone/skills/
  clone-recon/
    SKILL.md
    references/recon-template.md      plantilla de clone/recon.md
    references/android-capture.md     setup de adb, troubleshooting, limites
    references/windows-capture.md     setup de UIA, elevacion, limites
    scripts/capture_android.py        captura via adb (stdlib)
    scripts/capture_windows.ps1       captura via UI Automation (PowerShell 5.1, sin instalar nada)
    scripts/uitree.py                 normalize | summarize (incluye redaccion)
    tests/test_uitree.py
    tests/test_capture_android.py
    tests/fixtures/                   XML de uiautomator y JSON de UIA sinteticos
  clone-arch/
    SKILL.md
    references/stack-matrix.md        criterios, pesos y candidatos de stack
  clone-build/
    SKILL.md
  clone-diff/
    SKILL.md
    scripts/treediff.py               diff de dos arboles normalizados
    scripts/parity.py                 reporte de paridad y veredicto
    tests/test_treediff.py
    tests/test_parity.py
    tests/fixtures/
```

Todas las skills llevan `disable-model-invocation: true` (solo usuario).
Scripts Python: solo stdlib, Python 3.10+. En Windows se invocan con `python`.
Ruta de scripts en los SKILL.md: `${CLAUDE_SKILL_DIR}/scripts/...`; las skills
que usan scripts de otra skill del pack usan `${CLAUDE_SKILL_DIR}/../clone-recon/scripts/...`.

### 3.2 Carpeta de trabajo `clone/` (en el proyecto del clon)

```
clone/
  recon.md            mapa: alcance, fuentes, pantallas, flujos, componentes, modelo de datos, fuera de alcance, tamano
  screens.csv         inventario de pantallas y estados
  flows.csv           flujos con conteo de pasos
  features.csv        matriz de features
  architecture.md     stack + justificacion, modelo de datos, modulos, orden de construccion
  build-log.md        una linea por pantalla
  parity.md           reporte final de /clone-diff
  captures/
    original/<SID>.png  <SID>.raw.xml|raw.json  <SID>.tree.json
    clone/<SID>.png     <SID>.raw.*             <SID>.tree.json
  diffs/<SID>.json    salida de treediff --json
```

`<SID>` es el id de pantalla con estado opcional: `S03` o `S03@vacio`.
Los ids son estables: S01.. para pantallas, F01.. para flujos, K01.. para
features. Todos los archivos se refieren a ellos.

#### screens.csv

`id,nombre,como_llegar,estados,proposito,estado_clon`

- `estados`: lista separada por `|` (ej. `vacio|lleno|error`)
- `estado_clon`: `no | parcial | hecho`

#### flows.csv

`id,nombre,pantallas,pasos_original,pasos_clon`

- `pantallas`: secuencia separada por `>` (ej. `S01>S04>S05`)
- `pasos_*`: numero de interacciones (taps, clicks, teclas de envio) del camino feliz. `pasos_clon` vacio hasta medirlo.

#### features.csv

`id,feature,area,prioridad,pantallas,estado,notas`

- `prioridad`: `must | should | could | skip | extra`
  - `skip`: no se reconstruye (va con razon en `notas`)
  - `extra`: agregada por el usuario, no existe en el original
- `pantallas`: S-IDs separados por `|`
- `estado`: `no | parcial | si`

### 3.3 Arbol de UI normalizado (`*.tree.json`)

```json
{
  "schema": 1,
  "platform": "android | windows",
  "screen": "S03@vacio",
  "source": "com.example.app/.SettingsActivity | notepad.exe: Sin titulo - Bloc de notas",
  "captured_at": "2026-10-20T15:04:05Z",
  "window": {"w": 1080, "h": 2400},
  "tree_quality": "full | partial | none",
  "redacted": true,
  "root": {
    "role": "window",
    "name": "",
    "text": "",
    "id": "",
    "bounds": [0.0, 0.0, 1.0, 1.0],
    "enabled": true,
    "children": []
  }
}
```

- `bounds`: `[x, y, w, h]` relativos a la ventana, 0-1, 3 decimales.
- `name`: etiqueta accesible (content-desc, Name de UIA, hint).
- `text`: contenido visible (texto de TextView/EditText, Value de UIA).
- `id`: resource-id de Android (sin paquete) o AutomationId de UIA.
- `tree_quality`:
  - `full`: arbol obtenido y con al menos un nodo interactivo
  - `partial`: arbol obtenido pero sin nodos interactivos, o truncado por limite de profundidad
  - `none`: no se pudo obtener arbol (solo screenshot)

Vocabulario de roles (fijo):
`window, group, toolbar, button, link, input, select, checkbox, radio, switch,
slider, list, listitem, tabs, tab, menu, menuitem, text, image, unknown`

Roles interactivos (peso 3 en el diff): `button, link, input, select,
checkbox, radio, switch, slider, tab, menuitem, listitem`.
Roles de contenido (peso 1): `list, tabs, menu, toolbar, text, image, unknown`.
Contenedores (peso 0): `window, group`.

#### Mapeo Android (atributo `class` de uiautomator)

| clase (sufijo) | rol |
|---|---|
| Button, ImageButton, MaterialButton, FloatingActionButton | button |
| EditText, AutoCompleteTextView, TextInputEditText | input |
| CheckBox, CheckedTextView | checkbox |
| Switch, SwitchCompat, SwitchMaterial | switch |
| RadioButton | radio |
| SeekBar, Slider | slider |
| Spinner | select |
| RecyclerView, ListView, GridView | list |
| TabLayout | tabs |
| TabLayout$TabView, TabView | tab |
| TextView | text |
| ImageView | image |
| WebView | group |

Clase no listada (ej. `android.view.View` de Compose): `checkable=true` ->
checkbox; `clickable=true` -> button; `scrollable=true` -> list; con texto y
sin hijos -> text; con hijos -> group; resto -> unknown.
Hijo directo de un `list` con `clickable=true` -> listitem.

#### Mapeo Windows (ControlType de UIA)

| ControlType | rol |
|---|---|
| Button, SplitButton | button |
| Hyperlink | link |
| Edit, Document | input |
| ComboBox | select |
| CheckBox | checkbox |
| RadioButton | radio |
| Slider, Spinner | slider |
| List, DataGrid, Tree, Table | list |
| ListItem, DataItem, TreeItem | listitem |
| Tab | tabs |
| TabItem | tab |
| Menu, MenuBar | menu |
| MenuItem | menuitem |
| ToolBar | toolbar |
| Text | text |
| Image | image |
| Window | window |
| Pane, Group, Custom, StatusBar, Header, HeaderItem, Separator, ToolTip, Calendar, ProgressBar, SemanticZoom, AppBar y cualquier otro | group |

Cualquier nodo con TogglePattern cuyo ClassName contenga `ToggleSwitch` -> switch
(tiene prioridad sobre la tabla). ScrollBar, Thumb y TitleBar se descartan con
todo su subarbol en la normalizacion: son marco de ventana, no UI de la app
(verificado con el Bloc de notas: sin esto aparecen Minimizar/Maximizar/Cerrar
y el menu del sistema).

#### Normalizacion (en este orden)

1. Descartar nodos con area 0, fuera de la ventana, o `IsOffscreen=true` (UIA).
2. Descartar ScrollBar, Thumb y TitleBar con su subarbol.
3. Colapsar `group` sin nombre/texto/id con un solo hijo: el hijo sube.
4. Limite de profundidad: 25 por defecto (`--max-depth`). Si se trunca, `tree_quality=partial`.
5. Redaccion (activa por defecto, se desactiva con `--no-redact`):
   - emails -> `<email>`
   - secuencias de 7+ digitos con espacios, guiones, parentesis o `+` -> `<phone>`
   - numeros de 6+ digitos -> `<num>`
   - `text` de nodos con rol `input` -> `<value>` si no esta vacio (el `name`/hint se conserva)

### 3.4 Scripts: interfaces

#### capture_android.py

```
python capture_android.py --id S03@vacio --out clone/captures/original
       [--serial SERIAL] [--adb RUTA] [--max-depth 25] [--no-redact] [--retries 3]
```

- Localiza adb en: `--adb`, PATH, `%ANDROID_HOME%\platform-tools`,
  `%LOCALAPPDATA%\Android\Sdk\platform-tools`, `~/Android/Sdk/platform-tools`.
  Si no lo encuentra: exit 2 con el mensaje de instalacion.
- Si hay mas de un dispositivo en `adb devices` y no hay `--serial`: exit 2 listando los seriales.
- Ejecuta: `uiautomator dump /sdcard/clone_dump.xml` + leer el XML via `exec-out cat`,
  `exec-out screencap` (crudo, sin `-p`), `dumpsys activity activities` (linea
  `topResumedActivity` o `mResumedActivity`) para `source`.
- El screencap crudo es un header de 12 o 16 bytes (ancho, alto, formato y,
  desde Android 12, espacio de color) seguido de pixeles RGBA_8888. El script
  lo codifica a PNG con `zlib` (filtro 0). Formatos distintos de 1 y 2
  (RGBA/RGBX) dan exit 2. Se usa el crudo en vez de `-p` porque decodificar un
  PNG de 1080x2400 en Python puro para revisar sus pixeles tarda decenas de
  segundos; el crudo se compara en milisegundos.
- `uiautomator dump` fallido ("could not get idle state" u otro error): reintenta
  `--retries` veces con 1 s de espera; si sigue fallando, guarda solo el PNG y
  escribe el tree.json con `tree_quality=none`.
- Pantalla negra (FLAG_SECURE): se detecta si todos los pixeles del screencap
  crudo son iguales; se avisa por stderr y el PNG se conserva.
- Escribe `<SID>.png`, `<SID>.raw.xml`, `<SID>.tree.json` y por stdout el
  resumen de `uitree summarize`.
- El ejecutor de comandos es una funcion inyectable (`run(cmd) -> (code, stdout_bytes, stderr)`)
  para testear sin dispositivo.
- Exit: 0 ok, 1 captura parcial (tree_quality none o pantalla negra), 2 error de entorno.

#### capture_windows.ps1

```
powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1
           -Id S03@vacio -Out clone/captures/original
           (-Process notepad | -Title "Bloc de notas") [-MaxDepth 25]
```

- Carga `UIAutomationClient`, `UIAutomationTypes`, `System.Drawing`,
  `System.Windows.Forms` (todos vienen con Windows PowerShell 5.1).
- Encuentra la ventana principal por nombre de proceso o por titulo (contiene).
  Si hay varias coincidencias, toma la que tiene foco o la primera, y lo dice.
- Apps UWP/WinUI empaquetadas (ej. Calculadora) viven dentro de
  `ApplicationFrameHost.exe`: `-Process` no encuentra su ventana, por eso el
  mensaje de "ventana no encontrada" sugiere usar `-Title`.
- Recorre con `TreeWalker.ControlViewWalker` hasta `-MaxDepth`. Por nodo guarda:
  ControlType.ProgrammaticName, Name, AutomationId, ClassName,
  BoundingRectangle, IsEnabled, IsOffscreen, Value (si tiene ValuePattern) y
  Toggle (si tiene TogglePattern).
- Captura PNG del rectangulo de la ventana con `Graphics.CopyFromScreen`.
- Escribe `<SID>.raw.json` y `<SID>.png`. La normalizacion la hace
  `uitree.py normalize --from uia` (paso separado que la skill ejecuta).
- Acceso denegado (app elevada): exit 2 con el mensaje "ejecuta la terminal
  como administrador o captura solo screenshot".
- Sin controles visibles (todos los hijos de la ventana fuera de pantalla o de
  area 0: ventana recien abierta, minimizada u oculta): reintenta `-Retries`
  veces (3 por defecto) con 500 ms de espera. Si sigue igual, guarda la
  captura, avisa por stderr (con mensaje especifico si esta minimizada) y sale
  con exit 1. Agregado tras observar una captura vacia intermitente del Bloc
  de notas en la verificacion final.
- Exit: 0 ok, 1 captura parcial (sin controles visibles), 2 ventana no
  encontrada o acceso denegado.

#### uitree.py

```
python uitree.py normalize --from android|uia RAW --out TREE --screen SID
                 [--max-depth 25] [--no-redact]
python uitree.py summarize TREE [--max-lines 40]
```

`summarize` produce un esquema indentado, una linea por nodo no contenedor:
`rol "etiqueta" #id [x,y]`, con hermanos repetidos colapsados como
`listitem x12 (plantilla: text, text, image)`. Si excede `--max-lines`, corta
por profundidad y termina con `... N nodos mas`. Es lo que Claude lee, nunca el
raw.

#### treediff.py

```
python treediff.py ORIGINAL.tree.json CLON.tree.json [--json] [--ignore-text] [--out DIFF.json]
```

Algoritmo:

1. Si alguno tiene `tree_quality=none`: resultado `status: "skipped"`, sin score, exit 0.
2. Aplanar cada arbol a nodos con: rol, id, etiqueta (name o text, normalizada:
   minusculas, sin acentos, espacios colapsados), centro relativo, ruta de roles
   de ancestros.
3. Colapsar listas: los hijos de un `list` se agrupan por firma (rol + roles de
   todos sus descendientes en preorden); cada grupo queda como un solo nodo
   plantilla con `count` y no se desciende en el. Los hijos contenedores
   (`group`) de una lista no se puntuan. "Ruta de roles del padre" es el rol
   del ancestro no contenedor mas cercano (`root` si no hay).
4. Emparejamiento uno a uno, por pasadas, entre nodos del mismo rol:
   0. plantillas de lista con la misma firma (sin importar `count`)
   a. mismo `id` no vacio
   b. misma etiqueta no vacia (se omite con `--ignore-text`)
   c. distancia entre centros < 0.08 y mismo rol de padre
   Dentro de cada pasada, menor distancia de centros primero.
   Limitacion conocida de v1: un control que falta dentro de cada fila de una
   lista cambia la firma, pero la plantilla igual empareja por posicion (pasada
   c), asi que ese faltante no se reporta. Se revisa a mano en `/clone-diff`.
5. Scores:
   - `interactive_score` = peso emparejado / peso total del original, solo roles
     interactivos, 0-100 entero. Si el original no tiene interactivos: null.
   - `structure_score` = igual con roles interactivos + de contenido.
6. Reporte:
   - `missing`: nodos del original sin pareja (rol, etiqueta, bounds), primero interactivos
   - `extra`: nodos del clon sin pareja (informativo, no penaliza)
   - `text_changed`: emparejados por a o c con etiqueta distinta (informativo)
   - `moved`: emparejados con distancia de centros > 0.15 (informativo)

Salida de texto legible o `--json`. `--out DIFF.json` escribe el JSON en UTF-8
(para `clone/diffs/`) y sigue imprimiendo la version de texto. Exit 0 siempre que
pueda leer ambos archivos; 2 si un archivo no existe o no es schema 1.

Todos los scripts Python reconfiguran stdout/stderr con `errors="replace"`: en
una consola cp1252 un caracter no imprimible no tumba el script. Por la misma
razon los archivos se escriben con `--out` (UTF-8) y nunca con `>`, que en
Windows usa la codificacion de la consola y luego no se puede leer como UTF-8.

#### parity.py

```
python parity.py clone/ [--json | --markdown] [--out ARCHIVO]
```

`--out` escribe el reporte en UTF-8 e imprime `ok: ARCHIVO (veredicto X)`.

Lee `features.csv`, `flows.csv`, `diffs/*.json`.

- Feature score: pesos must 3, should 2, could 1; estado si 1, parcial 0.5,
  no 0; `skip` y `extra` excluidos. `round(100 * sum(w*s) / sum(w))`.
- Must faltantes: features `must` con estado distinto de `si`, listadas.
- Score por pantalla: `interactive_score` de cada diff; pantallas `skipped` se
  listan aparte como "solo features".
- Flujos: por fila con `pasos_clon`, delta contra el original.
- Veredicto:
  - `incompleto`: algun must no esta en `si`, o alguna pantalla con score < 70
  - `usable`: todos los must en `si` y ninguna pantalla con score < 70
  - `completo`: usable, feature score >= 90 y todas las pantallas con score >= 85
- Orden de "lo que falta": must, luego should, luego could; dentro de cada uno
  por area con menor score.
- Exit: 0 usable o completo, 1 incompleto, 2 error de entrada.

### 3.5 Skills: responsabilidades y pasos

#### /clone-recon

Entrada: nombre de la app, plataforma (android | windows), y como identificarla
(paquete, proceso o titulo de ventana).

1. Alcance: app, plataforma, el corte a reconstruir (por defecto el flujo
   principal que la hace util) y para quien.
2. Verificar entorno: adb y dispositivo (android) o ventana encontrada
   (windows). Si falla, seguir `references/*-capture.md`.
3. Fuentes publicas como complemento: ficha de Play Store o web, centro de
   ayuda, changelog. Tabla de fuentes con URL.
4. Bucle de captura: la skill pide "navega a <pantalla/estado> y dime listo",
   captura, lee el `summarize`, asigna SID y registra en `screens.csv`.
   Continua hasta cubrir el alcance. Estados minimos a pedir por pantalla:
   vacio, con datos, error si aplica.
5. Flujos: para cada objetivo del usuario dentro del alcance, la secuencia de
   pantallas y el conteo de pasos del camino feliz -> `flows.csv`.
6. Componentes repetidos (con sus variantes) -> seccion en `recon.md`.
7. Modelo de datos inferido: entidades, campos, relaciones, cada uno con
   evidencia (SIDs) y confianza (alta | media | supuesto).
8. Features -> `features.csv` con prioridad. Lo no reconstruible va como
   `skip` con razon: contenido licenciado, la red de usuarios, datos del
   servidor del original, hardware, integraciones privadas.
9. Tamano: S (un fin de semana), M (unas semanas), L (un trimestre), XL
   (re-acotar). Con las 3 partes mas dificiles.
10. Sugerir agregar `clone/captures/` a `.gitignore`.

Salida: `recon.md`, `screens.csv`, `flows.csv`, `features.csv`, capturas, y un
resumen de 5 lineas con siguiente paso `/clone-arch`.

#### /clone-arch

Entrada: `clone/recon.md`, `features.csv`. Sin recon: detenerse y pedir `/clone-recon`.

1. Stack con `references/stack-matrix.md`. Criterios y pesos:

   | criterio | peso |
   |---|---|
   | plataforma del original y donde se va a usar el clon | 3 |
   | integracion con el sistema (notificaciones, archivos, bandeja, servicios en segundo plano) | 2 |
   | offline / sincronizacion | 2 |
   | experiencia del usuario con el stack (Kotlin/Android pesa a favor) | 2 |
   | necesita Android y PC a la vez | 2 |
   | capturabilidad (expone arbol de UI para el diff) | 1 |

   Candidatos: Kotlin + Jetpack Compose (Android); Kotlin Multiplatform +
   Compose (Android + escritorio, capturabilidad baja en Windows); C# + WinUI 3
   o WPF (Windows); Tauri + web (escritorio, WebView2 expone UIA); app web
   local (navegador). Cada candidato puntuado 1-5 por criterio; se recomienda
   el de mayor total y se muestra la tabla. Si el elegido tiene capturabilidad
   baja, avisar que esas pantallas quedaran como "solo features" en el diff.
2. Modelo de datos: del inferido a esquema real (Room/SQLite segun stack):
   tipos, claves, indices, restricciones, migracion inicial.
3. Modulos y capas (Clean Architecture). En Android, validar con `/android-arch`
   una vez exista codigo.
4. Orden de construccion: hito 1 corte vertical del flujo principal (F01 de
   punta a punta, feo pero funcionando), luego must por area, luego should y
   could. Cada hito lista SIDs, tablas y features (K-IDs).

Salida: `architecture.md` y resumen con siguiente paso `/clone-build`.

#### /clone-build

Entrada: `architecture.md`, `recon.md`, `screens.csv`, `features.csv`,
capturas originales. Argumento opcional: hito o SID.

Por cada pantalla, en el orden de `architecture.md`:

1. Leer su fila en `screens.csv`, el `summarize` de su captura original y los
   flujos que pasan por ella.
2. Logica (ViewModel, casos de uso, repositorios) con `/tdd`.
3. UI con todos los estados del recon.
4. Correr el clon, llevarlo a la pantalla/estado y capturar con el mismo
   script a `clone/captures/clone/`.
5. `treediff.py` original vs clon con `--out clone/diffs/<SID>.json`.
6. Definicion de terminado:
   - todos los estados de la pantalla capturados en el clon
   - `interactive_score >= 85`, o cada `missing` justificado en `build-log.md`
   - tests de la logica pasan
   - `features.csv` y `screens.csv` actualizados
   - captura del clon guardada
7. Una linea en `build-log.md` y un commit por pantalla: `build(clone): S03 ajustes`.

Si una pantalla resulta mas grande de lo estimado, se dice en el chat y en el
log; no se entrega a medias en silencio.

Salida: pantallas hechas / total, must hechos / total, siguiente hito.

#### /clone-diff

1. Verificar que cada pantalla con estado `hecho` tiene diff; si falta, generarlo.
2. Pedir al usuario recorrer cada flujo en el clon y anotar `pasos_clon`.
3. `parity.py clone/ --markdown --out clone/parity.md`.
4. Revisar a mano los `missing` de las pantallas con menor score y los
   `text_changed` relevantes.
5. Presentar: veredicto, feature score, score por pantalla, flujos con delta,
   las 5 cosas que mas suben el score, y siguiente paso (`/clone-build` para
   huecos o terminar).

### 3.6 Reglas transversales (en los cuatro SKILL.md)

- Solo se observa la UI de una app instalada por el usuario en su dispositivo,
  mas fuentes publicas. No se descompilan APK/EXE, no se extraen recursos
  (iconos, imagenes, fuentes, strings) del paquete, no se intercepta trafico de
  red, no se usan APIs privadas del original.
- Las capturas son referencia y no se copian al clon.
- Nunca se pide ni se escribe una contrasena; si una pantalla requiere login,
  el usuario lo hace.
- Los numeros que se reportan salen de los scripts, no se estiman.

## 4. Casos edge

| caso | manejo |
|---|---|
| adb no instalado o no en PATH | busqueda en rutas conocidas; si no, exit 2 con instrucciones en `android-capture.md` |
| varios dispositivos | exit 2 listando seriales, pide `--serial` |
| `uiautomator dump` falla por animaciones | reintentos; luego `tree_quality=none` |
| FLAG_SECURE (pantalla negra) | aviso; el arbol suele funcionar y se conserva |
| juegos, Unity, Flutter con semantica pobre | `tree_quality` none o partial; la pantalla se evalua solo por features |
| app de Windows elevada | exit 2 con mensaje claro |
| varias ventanas que coinciden | se elige la de foco o la primera y se informa |
| app UWP/WinUI hospedada por ApplicationFrameHost | `-Process` falla; el mensaje sugiere `-Title` |
| arboles enormes (Electron) | descarte de offscreen, colapso de grupos, limite de profundidad |
| listas de distinto tamano | colapso a plantilla; no penaliza |
| textos traducidos o distintos | emparejamiento por id y posicion; reportado como `text_changed` sin penalizar |
| resolucion/DPI distintos, Android vs escritorio | bounds relativos; la pasada por posicion (c) es la unica que depende de layout |
| datos personales en capturas | redaccion por defecto + sugerencia de `.gitignore` |
| stack del clon poco capturable | aviso en `/clone-arch`; pantallas como "solo features" |
| features.csv mal formado (prioridad o estado invalido) | parity.py exit 2 indicando fila y valor |

## 5. Que se incluye y que se excluye

Incluye:
- las cuatro skills y sus referencias
- `capture_android.py`, `capture_windows.ps1`, `uitree.py`, `treediff.py`, `parity.py`
- tests unitarios de los scripts Python con fixtures sinteticos
- actualizacion de `CLAUDE.md` (estructura, tabla de skills, flujo) y `README.md`

Excluye (v1):
- rebrand, tiendas, analisis de resenas, deploy
- diff visual de screenshots (pixel o bordes)
- captura continua automatica (modo watch)
- Linux y macOS como plataforma objetivo (solo screenshots manuales sin arbol)
- iOS
- port a Codex (`.agents/skills/`)
- descompilacion, extraccion de recursos, captura de red (excluidos por regla, no solo por alcance)

## 6. Estrategia de testing

`unittest` de stdlib. Se corren con:

```
python -m unittest discover -s tests -v
python -m unittest discover -s tests -v
```

Casos minimos:

- uitree normalize android: fixture con Button, EditText, CheckBox, RecyclerView
  con 3 items, y un `android.view.View` clickable (Compose) -> roles esperados
  exactos; bounds relativos correctos a 3 decimales.
- uitree normalize uia: fixture con Window, Edit, Button, List con ListItems,
  ScrollBar, nodo offscreen -> roles esperados; ScrollBar y offscreen descartados.
- normalizacion: group sin etiqueta con un hijo se colapsa; arbol de 30 niveles
  con `--max-depth 25` -> `tree_quality=partial`.
- redaccion: email, telefono `+57 300 123 4567`, numero `123456`, valor de input;
  con `--no-redact` quedan intactos.
- summarize: lista de 12 items iguales sale como una linea `x12`; respeta `--max-lines`.
- capture_android con ejecutor falso: dos dispositivos sin serial -> exit 2;
  dump fallido 3 veces -> `tree_quality=none` y exit 1; PNG de un color -> aviso
  y exit 1; caso feliz -> tres archivos y exit 0.
- treediff: arboles identicos -> 100/100; original con un button que el clon no
  tiene -> ese button en `missing` y score esperado exacto; hermanos reordenados
  -> 100; lista 3 vs 20 items -> sin `missing`; etiqueta cambiada con mismo id ->
  100 y un `text_changed`; `--ignore-text` desactiva la pasada b; uno con
  `tree_quality=none` -> `skipped`.
- parity: fixture con must/should/could/skip/extra y parciales -> score exacto
  esperado; must faltante -> `incompleto` y exit 1; caso usable y caso completo
  en sus umbrales exactos (70/85/90); fila con prioridad invalida -> exit 2.

Verificacion manual (documentada, no automatizada):
- `capture_windows.ps1` contra Bloc de notas y Calculadora de Windows.
- `capture_android.py` contra un dispositivo real cuando haya adb instalado.

## 7. Criterios de verificacion

1. Las dos suites de tests pasan con 0 fallos y 0 errores.
2. `capture_windows.ps1 -Process notepad` produce `raw.json` y `png`; tras
   `normalize`, el tree.json tiene al menos 1 nodo `input` y `tree_quality=full`.
3. `capture_windows.ps1 -Title "Calculadora"` ("Calculator" si Windows esta en
   ingles) produce, tras `normalize`, un tree.json con al menos 10 nodos `button`.
4. `treediff.py` de la captura de Bloc de notas contra si misma da
   `interactive_score` 100.
5. Los cuatro SKILL.md tienen frontmatter valido con `name`, `description`,
   `when_to_use`, `argument-hint`, `disable-model-invocation: true` y `allowed-tools`.
6. `CLAUDE.md` lista las cuatro skills en la estructura, la tabla y un flujo
   `/clone-recon -> /clone-arch -> /clone-build -> /clone-diff`.
7. Ningun archivo del pack contiene emojis ni referencias a repos o proyectos
   externos como origen.
8. Todos los scripts Python importan solo modulos de la stdlib (verificable
   con un grep de `import`).
