---
name: clone-arch
description: >
  Elige el stack del clon con una matriz de decision ponderada, convierte el
  modelo de datos inferido del recon en un esquema real, define modulos y
  capas, y fija el orden de construccion empezando por un corte vertical del
  flujo principal. Segundo paso del clone pack.
when_to_use: >
  Cuando el usuario dice "clone-arch", "que stack uso para el clon",
  "disena la arquitectura del clon", o despues de /clone-recon.
argument-hint: "[ruta al proyecto del clon]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Clone Arch — Stack, datos y orden de construccion

Lee `clone/recon.md`, `clone/screens.csv`, `clone/flows.csv` y
`clone/features.csv`. Escribe `clone/architecture.md`.

Si no existe `clone/recon.md`: detenerse y pedir `/clone-recon`. Planear un
clon de memoria es como se pierde la mitad de la app.

## Paso 1: stack

Puntuar los candidatos con `references/stack-matrix.md` y mostrar la tabla
completa. Recomendar el de mayor total con una linea de por que. Si el usuario
ya tiene un stack decidido, usarlo y solo marcar los riesgos que la matriz
detecta.

Si el elegido tiene capturabilidad 2 o menos, avisar: las pantallas del clon
quedaran como "solo features" en `/clone-diff` y la paridad de UI no se podra
medir.

## Paso 2: modelo de datos

Del modelo inferido en `recon.md` a un esquema real para el stack elegido
(Room en Android, SQLite/EF Core en .NET, SQLite en Tauri o web local):

- clave primaria por tabla, y `created_at`/`updated_at` si el original
  muestra fechas
- claves foraneas con regla de borrado decidida, no por defecto
- indices en cada clave foranea y en cada columna por la que se filtra u
  ordena en alguna pantalla
- estados como enum o restriccion check
- fechas en UTC, mostradas en la zona del usuario
- los campos con confianza `supuesto` se marcan en el esquema con un comentario
- migracion inicial escrita

## Paso 3: modulos y capas

Clean Architecture: `domain` (entidades y casos de uso, sin framework),
`data` (repositorios, base de datos), `ui` (pantallas y ViewModels). Un modulo
o paquete de feature por area de `features.csv` cuando hay mas de 3 areas.
En Android, cuando exista codigo, validar con `/android-arch`.

## Paso 4: partes delicadas

Una linea por cada una que aplique: sincronizacion, offline, notificaciones,
tareas en segundo plano, archivos grandes, busqueda, integraciones con el
sistema (bandeja, inicio automatico, atajos globales), permisos de Android.

## Paso 5: orden de construccion

1. **Hito 1, corte vertical:** el flujo F01 de punta a punta, feo pero
   funcionando. Prueba el stack.
2. **Must** de `features.csv`, agrupados por area.
3. **Should**, luego **could**.

Cada hito lista sus SIDs, tablas y K-IDs, en el orden en que `/clone-build`
los va a construir.

## Salida

`clone/architecture.md` con: tabla de la matriz y stack elegido, esquema,
modulos, partes delicadas y orden de construccion. Resumen: stack en una
linea, numero de tablas, numero de hitos, las 3 partes mas riesgosas, y
siguiente paso: `/clone-build`.
