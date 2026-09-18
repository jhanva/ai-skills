---
name: design-system
description: >
  Decide y persiste el sistema de diseno de un producto antes de construir UI:
  estilo, paleta con contraste validado, tipografia, escala de espaciado, motion,
  checklist de accesibilidad y reglas del stack (Jetpack Compose o web). Consulta
  un catalogo local con buscador; no improvisa colores ni estilos. Genera
  design-system/<proyecto>/MASTER.md y overrides por pantalla.
  Usar cuando: el usuario dice "design system", "sistema de diseno", "define la
  paleta", "que estilo usamos", "tokens de diseno", o va a construir la primera
  pantalla de un producto nuevo.
argument-hint: "[descripcion del producto] [--stack compose|web] [--page nombre]"
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

## Herramienta

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<consulta>" --design-system -p "<Proyecto>" --stack <compose|web>
```

Si `python` no existe, probar `python3` y despues `py -3`. Python 3.x sin dependencias.
Exit codes: 0 ok, 1 sin resultados, 2 uso invalido, 3 se nego a sobreescribir, 4 error.

## FASE 1: Entender el producto

Extraer de la peticion y del repositorio:

| Dato | Como obtenerlo |
|---|---|
| Tipo de producto | Lo que dice el usuario: fintech, salud, comercio, herramienta interna, media... |
| Audiencia y contexto | Uso experto y prolongado vs ocasional; movil en la calle vs desktop en oficina |
| Stack | `build.gradle(.kts)` con `compose` -> `compose`; `package.json` o `index.html` -> `web`. Si hay ambos o ninguno: preguntar |
| Sistema previo | `Glob design-system/**/MASTER.md`. Si existe: **leerlo** y trabajar sobre el, no regenerar |

Construir la consulta con 2-5 terminos que nombren dominio, tipo de interfaz y tono
(`"app de salud pacientes citas calma"`, `"dashboard interno logistica datos densos"`).

## FASE 2: Generar y revisar

1. Ejecutar el script **sin** `--persist` y leer el markdown.
2. Comprobar que el estilo, la paleta y la tipografia encajan con el producto. Si el output dice
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
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<consulta>" --design-system -p "<Proyecto>" --stack <stack> --persist --output-dir "<raiz del proyecto>"
```

Crea `design-system/<slug>/MASTER.md`. Es la fuente de verdad global: `/plan`, `/execute` y
`/ui-tokens` la leen antes de tocar UI.

### Overrides por pantalla

Cuando una pantalla necesita reglas distintas (un dashboard denso dentro de una app espaciosa):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<consulta de la pantalla>" --design-system -p "<Proyecto>" --stack <stack> --persist --output-dir "<raiz>" --page "<nombre>"
```

Crea `design-system/<slug>/pages/<nombre>.md` sin tocar `MASTER.md`. Regla de lectura: si
existe el archivo de la pantalla, sus secciones sustituyen a las de MASTER; lo que no aparece
hereda de MASTER.

### Cambiar un sistema existente

Si el usuario pide regenerar: leer el `MASTER.md` actual, listar que cambiaria, y solo con su
autorizacion ejecutar con `--force`. Un sistema en uso tiene decisiones tomadas por personas;
no se pisan en silencio.

## FASE 4: Cerrar

Reportar: ruta escrita, resumen de decisiones, valores sin match verificado (si los hubo) y el
siguiente paso sugerido (`/plan` de la primera pantalla o `/ui-tokens` para materializar tokens).

Argumento recibido: $ARGUMENTS
