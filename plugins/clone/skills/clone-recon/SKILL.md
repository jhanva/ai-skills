---
name: clone-recon
description: >
  Desarma una app Android o Windows instalada en pantallas, flujos y features.
  Usar para empezar a reconstruir una app.
argument-hint: "[app] [android|windows] [paquete, proceso o titulo de ventana]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(python:*)
  - Bash(powershell:*)
  - Bash(adb:*)
---

# Clone Recon — Desarmar la app original

Todo el pack construye sobre lo que esta skill escribe. Un recon pobre da un
clon pobre: aqui se invierte el tiempo.

Scripts, con rutas relativas al directorio de esta skill (resolverlas a ruta
absoluta antes de ejecutar; en Windows usar `python`, en macOS/Linux `python3`):

```
scripts/capture_android.py   captura via adb
scripts/capture_windows.ps1  captura via UI Automation
scripts/uitree.py            normalize | summarize
```

## Reglas

- **Solo observar la UI.** La app instalada por el usuario en su dispositivo
  y fuentes publicas. Nunca descompilar APK/EXE, nunca extraer recursos del
  paquete (iconos, imagenes, fuentes, strings), nunca interceptar trafico de
  red, nunca usar APIs privadas del original.
- **El usuario navega y hace login.** Nunca pedir ni escribir contrasenas.
- **Leer el resumen, no el raw.** Despues de cada captura se lee la salida de
  `summarize` (unas 40 lineas). Nunca cargar `*.raw.xml` o `*.raw.json`.
- **Las capturas son referencia.** No se copian al clon.
- **Los numeros salen de los scripts.** No estimar conteos.

## Salida (en el proyecto del clon)

```
clone/recon.md        plantilla: references/recon-template.md
clone/screens.csv     id,nombre,como_llegar,estados,proposito,estado_clon
clone/flows.csv       id,nombre,pantallas,pasos_original,pasos_clon
clone/features.csv    id,feature,area,prioridad,pantallas,estado,notas
clone/captures/original/<SID>.png|.raw.*|.tree.json
```

`<SID>` es `S03` o `S03@estado`. Ids estables: S01.. pantallas, F01.. flujos,
K01.. features. Prioridad: `must | should | could | skip | extra`. Estado de
feature: `no | parcial | si`. Estado de pantalla: `no | parcial | hecho`.

## Paso 1: alcance

Preguntar una cosa a la vez, o proponer y pedir un si:

1. App y plataforma (android | windows) y como identificarla: paquete
   Android, nombre de proceso, o titulo de ventana.
2. El corte: por defecto el flujo principal que hace util a la app. "Toda la
   app" no es un alcance.
3. Para quien es el clon (el usuario, su equipo).

## Paso 2: entorno

- **Android:** `python scripts/capture_android.py --help`
  y luego una captura de prueba. Si falla, seguir `references/android-capture.md`.
- **Windows:** captura de prueba con `-Process` o `-Title`. Si falla, seguir
  `references/windows-capture.md`.

Sugerir agregar `clone/captures/` al `.gitignore` del proyecto: las capturas
pueden tener datos personales aunque se redacten.

## Paso 3: fuentes publicas

Tabla en `recon.md` con URL por fila: ficha de Play Store o web oficial,
centro de ayuda, changelog. El centro de ayuda es la lista de features mas
completa que existe; el changelog dice que considera importante el equipo.

## Paso 4: bucle de captura

Por cada pantalla y estado dentro del alcance:

1. Pedir: "Navega a <pantalla> en estado <estado> y dime listo."
2. Capturar:
   - Android:
     `python scripts/capture_android.py --id S03@vacio --out clone/captures/original`
   - Windows:
     `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/capture_windows.ps1 -Id S03@vacio -Out clone/captures/original -Process <proceso>`
     y luego
     `python scripts/uitree.py normalize --from uia clone/captures/original/S03@vacio.raw.json --out clone/captures/original/S03@vacio.tree.json --screen S03@vacio`
     y `python scripts/uitree.py summarize clone/captures/original/S03@vacio.tree.json`
3. Leer el resumen y el PNG. Registrar la fila en `screens.csv`.
4. Exit 1 de captura (sin arbol o pantalla negra): anotar en la fila que la
   pantalla sera "solo features" y seguir.

Estados minimos a pedir por pantalla: vacio, con datos, error si aplica. Un
estado que no se capturo es un estado que no se construye.

## Paso 5: flujos

Por cada objetivo del usuario dentro del alcance, en `flows.csv`: la
secuencia de pantallas (`S01>S04>S05`) y los pasos del camino feliz (taps,
clicks, teclas de envio). En `recon.md`, los casos edge de cada flujo.

## Paso 6: componentes

Partes de UI repetidas (botones, campos, listas, dialogos, menus): nombre,
variantes, estados, pantallas donde aparecen. Seccion en `recon.md`.

## Paso 7: modelo de datos inferido

Entidades, campos y relaciones, cada uno con evidencia (SIDs, articulos de
ayuda) y confianza: `alta | media | supuesto`. Lo que se adivina se marca
como supuesto.

## Paso 8: features

`features.csv`, una fila por feature con prioridad y SIDs. Lo que no se puede
reconstruir va como `skip` con la razon en `notas`: contenido licenciado, la
red de usuarios, datos del servidor del original, hardware, integraciones
privadas. `estado` empieza en `no`.

## Paso 9: tamano

Pantallas, flujos, entidades y las 3 partes mas dificiles (sincronizacion,
tiempo real, integraciones, offline, multimedia). Tamano: S (un fin de
semana), M (unas semanas), L (un trimestre), XL (re-acotar el corte).

## Cierre

Resumen de 5 lineas: el flujo principal, conteo de pantallas y flujos, las 3
partes dificiles, lo que queda fuera, y siguiente paso: `skill clone-arch`.
