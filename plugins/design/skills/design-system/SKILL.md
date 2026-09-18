---
name: design-system
description: >
  Decide y persiste el sistema de diseno de un producto antes de construir UI:
  modo por superficie (persuadir, operar, leer, experimentar), estilo, paleta con
  contraste validado, tipografia, escala de espaciado, motion, checklist de
  accesibilidad y reglas del stack (Jetpack Compose o web). Consulta un catalogo
  local con buscador; no improvisa colores ni estilos. Genera
  design-system/<proyecto>/PRODUCT.md (verdad del producto), MASTER.md (look) y
  overrides por pantalla.
  Usar cuando: el usuario dice "design system", "sistema de diseno", "define la
  paleta", "que estilo usamos", "tokens de diseno", o va a construir la primera
  pantalla de un producto nuevo.
argument-hint: "[descripcion del producto] [--stack compose|web] [--mode persuadir|operar|leer|experimentar] [--page nombre]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
---

# Design System — Decidir antes de dibujar

El objetivo es que ninguna pantalla nazca con colores, tamanos o animaciones inventados
sobre la marcha. Primero se decide el sistema, se persiste en el proyecto, y despues
`/plan` y `/execute` lo leen como fuente de verdad.

## Ley de hierro

- **Nunca sobreescribir `MASTER.md` sin autorizacion explicita del usuario.** El script se
  niega (exit 3) salvo con `--force`; ese flag solo se pasa cuando el usuario lo pide.
- **No inventar valores.** Si el catalogo no tiene match verificado, el output lo marca y se
  presenta al usuario como valor neutral por defecto, no como recomendacion.
- **No adivinar el stack.** Se detecta o se pregunta.
- **Una sola pregunta.** Si la lectura del producto es ambigua, se hace exactamente una pregunta
  (la que mas cambia el resultado), no un cuestionario. Si se puede inferir con confianza, no se pregunta.

## Herramienta

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<consulta>" --design-system -p "<Proyecto>" --stack <compose|web> [--mode <modo>]
```

Sin `--mode` el script lo infiere de la consulta y lo marca `(inferido)`; si no puede, asume
`operar` y lo avisa en el markdown. Pasar `--mode` con lo decidido en el Design Read.

Si `python` no existe, probar `python3` y despues `py -3`. Python 3.x sin dependencias.
Exit codes: 0 ok, 1 sin resultados, 2 uso invalido, 3 se nego a sobreescribir, 4 error.

## FASE 1: Leer el producto

Extraer de la peticion y del repositorio:

| Dato | Como obtenerlo |
|---|---|
| Tipo de producto | Lo que dice el usuario: fintech, salud, comercio, herramienta interna, media... |
| Audiencia y contexto | Uso experto y prolongado vs ocasional; movil en la calle vs desktop en oficina |
| Superficie y modo | Que pantalla se disena y que significa exito para quien la visita (tabla abajo) |
| Stack | `build.gradle(.kts)` con `compose` -> `compose`; `package.json` o `index.html` -> `web`. Si hay ambos o ninguno: preguntar |
| Sistema previo | `Glob design-system/**/{PRODUCT,MASTER}.md`. Si existen: **leerlos** y trabajar sobre ellos, no regenerar |

### Modo por superficie

El modo se elige por la **superficie pedida**, no por el producto: la landing de una herramienta es
`persuadir`; su documentacion es `leer`; su panel es `operar`.

| Modo | Exito del visitante | Que gana en el desempate |
|---|---|---|
| `persuadir` | Decide y actua (landing, marketing, pricing) | Expresion: una idea por seccion, CTA en el primer viewport, reglas `comp-*` completas |
| `operar` | Completa una tarea (app, dashboard, formularios, admin) | Escaneabilidad, consistencia, expectativas nativas; la marca vive en los detalles |
| `leer` | Entiende algo (docs, articulos, ayuda) | Comprension: estructura navegable, medida 60-75 caracteres |
| `experimentar` | Esta dentro de la obra (portfolio, galeria) | El artefacto manda; la interfaz retrocede |

### Design Read (obligatorio antes de ejecutar nada)

Declarar en **una linea** como se leyo el pedido y esperar objecion:

> Leo esto como: `<superficie>` en modo `<modo>` para `<audiencia>`, con tono `<2-3 palabras>`, stack `<compose|web>`.

Si la lectura diverge de verdad en un punto (por ejemplo, calmo vs energico), una sola pregunta.
Nunca arrancar con el default del modelo (gradientes, tres tarjetas iguales, eyebrow en cada
seccion, tipografia neutra en todo): el Design Read existe para decidir a proposito.

Construir la consulta con 2-5 terminos que nombren dominio, superficie y tono
(`"app de salud pacientes citas calma"`, `"landing saas desarrolladores sobria"`).

## FASE 2: Generar y revisar

1. Ejecutar el script **sin** `--persist` y leer el markdown.
2. Comprobar que el modo, el estilo, la paleta y la tipografia encajan con el Design Read. Si el output dice
   `Sin match verificado para: ...`, reformular la consulta una vez con terminos mas concretos.
   Si sigue sin match, decirlo al usuario y ofrecer el valor neutral como punto de partida.
3. Ajustar con busquedas puntuales si hace falta:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<terminos>" --domain <style|palette|typography|ux|motion> -n 3
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<terminos>" --stack <compose|web> -n 3
```

4. Presentar al usuario un resumen de 6-8 lineas (estilo, paleta, tipografia, espaciado, motion,
   reglas de stack) y las decisiones que quedaron sin match. Esperar su conformidad.

## FASE 3: Persistir

Con la conformidad del usuario:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<consulta>" --design-system -p "<Proyecto>" --stack <stack> --mode <modo> --persist --output-dir "<raiz del proyecto>" --audience "<quien>" --context "<donde y cuando lo usa>" [--voice "<tono>"] [--constraints "<regulatorio, marca, a11y>"]
```

Crea dos archivos en `design-system/<slug>/`:

- `PRODUCT.md` — verdad durable del producto: audiencia, contexto de uso, voz, restricciones y
  la lista de superficies con su modo. Cambia poco; **nunca se sobreescribe** (si existe, se edita
  a mano y se anade la superficie nueva a su lista).
- `MASTER.md` — el look: modo, estilo, color, tipografia, espaciado, motion, checklist y reglas de
  stack. Es la fuente de verdad visual que `/plan`, `/execute` y `/ui-tokens` leen antes de tocar UI.

`--audience` y `--context` salen del Design Read; si `/brainstorm` ya produjo una spec con esa
informacion, se copia de ahi.

### Overrides por pantalla

Cuando una pantalla necesita reglas distintas (un dashboard denso dentro de una app espaciosa):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<consulta de la pantalla>" --design-system -p "<Proyecto>" --stack <stack> --persist --output-dir "<raiz>" --page "<nombre>"
```

Crea `design-system/<slug>/pages/<nombre>.md` sin tocar `MASTER.md`. Una pantalla puede tener
**otro modo** que MASTER (la landing `persuadir` de una app `operar`): pasar `--mode` y anadir la
superficie a la lista de `PRODUCT.md`. Regla de lectura: si existe el archivo de la pantalla, sus
secciones sustituyen a las de MASTER; lo que no aparece hereda de MASTER.

### Cambiar un sistema existente

Si el usuario pide regenerar: leer el `MASTER.md` actual, listar que cambiaria, y solo con su
autorizacion ejecutar con `--force`. Un sistema en uso tiene decisiones tomadas por personas;
no se pisan en silencio.

## FASE 4: Cerrar

Reportar: rutas escritas, Design Read final, resumen de decisiones, valores sin match verificado
(si los hubo) y el siguiente paso sugerido (`/plan` de la primera pantalla o `/ui-tokens` para materializar tokens).

Argumento recibido: $ARGUMENTS
