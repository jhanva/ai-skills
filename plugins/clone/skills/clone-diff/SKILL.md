---
name: clone-diff
description: >
  Mide la paridad del clon con el original y da un veredicto. Usar para saber
  cuanto le falta al clon.
argument-hint: "[ruta a clone/]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash(python:*)
  - Bash(python3:*)
---

# Clone Diff — Paridad con evidencia

Scripts, con rutas relativas al directorio de esta skill (resolverlas a ruta
absoluta antes de ejecutar; en Windows usar `python`, en macOS/Linux `python3`):

```
scripts/treediff.py   ORIGINAL.tree.json CLON.tree.json [--json] [--ignore-text] [--out DIFF.json]
scripts/parity.py     clone/ [--json | --markdown] [--out ARCHIVO]
```

Para escribir archivos usar siempre `--out` (UTF-8), nunca `>`: en Windows la
redireccion usa la codificacion de la consola y rompe los acentos.

## Que significa paridad aqui

El clon hace el mismo trabajo, no se ve igual. El **feature score** es el
numero principal: si el usuario puede hacer todo lo que hacia en el original.
El **score de arbol** mide si cada pantalla tiene los mismos controles en la
misma estructura. Los textos distintos y los controles extra no penalizan:
son decisiones del clon.

## Paso 1: diffs al dia

Para cada fila de `clone/screens.csv` con `estado_clon` `hecho` o `parcial` y
cada estado capturado, verificar que existe `clone/diffs/<SID>.json` y que es
mas nuevo que las dos capturas. Si falta o esta viejo:

```
python scripts/treediff.py clone/captures/original/<SID>.tree.json clone/captures/clone/<SID>.tree.json --out clone/diffs/<SID>.json
```

Si falta la captura del clon, pedir que se capture (ver `skill clone-build` paso 5).

## Paso 2: pasos por flujo

Para cada fila de `clone/flows.csv` sin `pasos_clon`: pedir al usuario que
recorra el flujo en el clon y cuente taps/clicks/teclas de envio del camino
feliz. Anotarlo en la columna.

## Paso 3: reporte

```
python scripts/parity.py clone/ --markdown --out clone/parity.md
python scripts/parity.py clone/
```

Exit 1 significa veredicto `incompleto` (no es un error). Exit 2 es un
problema en `features.csv` o `flows.csv`: el mensaje dice fila y valor.

Pesos y umbrales:

- features: must 3, should 2, could 1; `si` 1, `parcial` 0.5, `no` 0;
  `skip` y `extra` no cuentan
- **incompleto:** algun must no esta en `si`, o alguna pantalla bajo 70
- **usable:** todos los must en `si` y todas las pantallas en 70 o mas
- **completo:** usable, feature score 90 o mas y todas las pantallas en 85 o mas
- pantallas `skipped` (sin arbol): se listan como "solo features"

## Paso 4: revision a mano

Para las 3 pantallas con menor score, leer la version de texto del diff:

```
python scripts/treediff.py clone/captures/original/<SID>.tree.json clone/captures/clone/<SID>.tree.json
```

Clasificar cada faltante: falta de verdad (va a la lista), existe con otro
rol o en otra pantalla (anotar, no es falta), o fue descartado a proposito
(anotar en `build-log.md`). Si un falso faltante se repite porque el clon no
tiene ids estables, recomendarlos (ver `skill clone-build` paso 3).

## Salida

Presentar con los numeros de `parity.py`, sin redondear ni estimar:

1. Veredicto, feature score y must hechos / total.
2. Score por pantalla, de menor a mayor, y las pantallas "solo features".
3. Flujos con delta de pasos (negativo es mejor que el original).
4. Las 5 cosas que mas suben el score: primero must pendientes, luego
   faltantes interactivos de las pantallas mas bajas.
5. Siguiente paso: `skill clone-build <SID o hito>` para los huecos, o terminado
   si el veredicto es `completo`.
