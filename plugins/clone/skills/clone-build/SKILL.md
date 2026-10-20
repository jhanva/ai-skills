---
name: clone-build
description: >
  Construye el clon pantalla por pantalla y compara cada una con el original.
  Usar despues de definir la arquitectura del clon.
argument-hint: "[hito | SID]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# Clone Build — Pantalla por pantalla contra el original

Lee `clone/architecture.md`, `clone/recon.md`, `clone/screens.csv`,
`clone/features.csv` y los resumenes de `clone/captures/original/`. Actualiza
`screens.csv`, `features.csv` y `clone/build-log.md`.

Scripts del pack, con rutas relativas al directorio de esta skill (resolverlas
a ruta absoluta antes de ejecutar):

```
../clone-recon/scripts/capture_android.py
../clone-recon/scripts/capture_windows.ps1
../clone-recon/scripts/uitree.py
../clone-diff/scripts/treediff.py
```

Sin `clone/architecture.md`: detenerse y pedir `skill clone-arch`.

## Reglas

- **Codigo propio.** Todo se escribe aqui a partir del recon. Nunca copiar
  recursos, codigo ni assets del original.
- **Logica con `skill tdd`.** ViewModels, casos de uso y repositorios: test que
  falla primero.
- **Leer resumenes, no raws.** `uitree.py summarize` sobre la captura original.
- **Un commit por pantalla:** `build(clone): S03 ajustes`.

## Ciclo por pantalla

Argumento: un hito (`hito 2`) o un SID (`S03`). Sin argumento: la siguiente
pantalla con `estado_clon` distinto de `hecho` en el orden de
`architecture.md`.

1. **Contexto.** Fila de `screens.csv`, resumen de cada estado capturado
   (`uitree.py summarize clone/captures/original/<SID>.tree.json`), flujos de
   `flows.csv` que pasan por ella, features (K-IDs) que la mencionan.
2. **Logica** con `skill tdd`.
3. **UI** con todos los estados del recon. En el stack, dar ids estables a los
   elementos interactivos (`testTag`/`contentDescription` en Compose,
   `AutomationProperties.AutomationId` en WinUI/WPF, `id`/`aria-label` en web):
   el diff los usa para emparejar.
4. **Correr el clon** y llevarlo a la pantalla y estado. Pedir al usuario que
   navegue si hace falta.
5. **Capturar el clon** con el mismo script que el original, a
   `clone/captures/clone/` y con el mismo SID.
6. **Diff:**
   `python ../clone-diff/scripts/treediff.py clone/captures/original/<SID>.tree.json clone/captures/clone/<SID>.tree.json --out clone/diffs/<SID>.json`
   Escribe el JSON (UTF-8) para `skill clone-diff` e imprime la version de texto
   con los faltantes. No redirigir con `>`: en Windows rompe los acentos.
7. **Definicion de terminado:**
   - [ ] todos los estados de la pantalla capturados en el clon
   - [ ] `interactive_score >= 85`, o cada faltante justificado en `build-log.md`
   - [ ] tests de la logica pasan
   - [ ] `features.csv` (estado `si` o `parcial` con nota) y `screens.csv`
         (`estado_clon`) actualizados
   - [ ] captura del clon guardada
8. **Log y commit.** Una linea en `build-log.md`:
   `S03 | 2026-10-20 | hecho | interactivo 92 | falta: atajo de teclado`.
   Luego el commit de la pantalla.

Un diff `skipped` (arbol `none` en original o clon) no bloquea: la pantalla
se cierra solo por features y se anota en el log.

## Cuando una pantalla es mas grande de lo estimado

Decirlo en el chat y en el log antes de seguir. No entregar media pantalla en
silencio. Proponer partirla: lo que entra en este hito y lo que pasa al
siguiente.

## Cuando no se entiende como funciona algo del original

Volver al original como usuario: centro de ayuda, el changelog, o pedir al
usuario que lo repita en su dispositivo y capturar el estado que falta. Nunca
descompilar ni mirar su trafico.

## Salida

Por pantalla: score y faltantes. Al cerrar un hito: pantallas hechas /
total, must hechos / total, y siguiente hito. Cuando no quedan pantallas:
siguiente paso `skill clone-diff`.
