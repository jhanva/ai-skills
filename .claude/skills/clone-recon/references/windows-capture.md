# Captura Windows

## Requisitos

Ninguno extra: Windows PowerShell 5.1 trae UI Automation y System.Drawing.
La ventana debe estar abierta, visible y no minimizada.

## Uso

```
powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone/captures/original -Process notepad
powershell -NoProfile -ExecutionPolicy Bypass -File capture_windows.ps1 -Id S03 -Out clone/captures/original -Title "Calculadora"
python uitree.py normalize --from uia clone/captures/original/S03.raw.json --out clone/captures/original/S03.tree.json --screen S03
python uitree.py summarize clone/captures/original/S03.tree.json
```

`-Process` es el nombre del proceso sin `.exe` (ver el Administrador de
tareas, pestana Detalles). `-Title` busca ventanas cuyo titulo contenga el
texto. `-MaxDepth` (25 por defecto) limita la profundidad del recorrido.
`-Retries` (3 por defecto) reintenta cada 500 ms si la ventana todavia no
muestra controles visibles. Exit 0 ok, 1 captura parcial (sin controles
visibles: se guarda igual y la pantalla queda como solo features), 2 ventana
no encontrada o acceso denegado.

## Problemas conocidos

| sintoma | causa | que hacer |
| --- | --- | --- |
| "ventana no encontrada" con `-Process` en una app de la Tienda | las apps UWP/WinUI viven dentro de `ApplicationFrameHost.exe` | usar `-Title` |
| exit 1 "sin controles visibles ... minimizada" | la ventana esta minimizada | restaurarla y repetir |
| exit 1 "sin controles visibles ... oculta" | ventana recien abierta, en otro escritorio virtual o cargando | traerla al frente, esperar a que cargue y repetir, o subir `-Retries` |
| "N ventanas coinciden" | varias instancias o titulos parecidos | se usa la que tiene foco; dar foco a la correcta antes de capturar |
| "acceso denegado" | la app corre como administrador | abrir la terminal como administrador o capturar solo screenshot |
| arbol casi vacio | juego DirectX/OpenGL, app Java/Swing sin Java Access Bridge, UI dibujada a mano | `tree_quality` partial o none: la pantalla se evalua solo por features |
| arbol enorme (Electron, navegadores) | cada div expone un nodo | normal: `uitree` descarta lo fuera de pantalla y colapsa grupos vacios |
| screenshot con otra ventana encima | `CopyFromScreen` copia lo que se ve | traer la ventana al frente y repetir |

## Clones web

Un clon web abierto en una pestana normal del navegador incluye en el arbol
la UI del navegador (pestanas, barra de direcciones). Para capturarlo limpio,
abrirlo como ventana de app: `chrome --app=http://localhost:3000` o
`msedge --app=http://localhost:3000`, y capturar por `-Title`. Un clon Tauri
o cualquier app con WebView2 expone su contenido por UI Automation sin pasos
extra.

## Que se descarta al normalizar

Barras de titulo (`TitleBar`), barras de desplazamiento (`ScrollBar`,
`Thumb`), nodos fuera de pantalla, nodos de area 0 y grupos sin nombre con un
solo hijo. Los botones Minimizar/Maximizar/Cerrar de apps con barra de titulo
propia (UWP) se conservan: aparecen igual en original y clon si ambos son
apps de Windows.
