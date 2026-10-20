# Matriz de stack

Cada candidato se puntua de 1 a 5 por criterio. Total = suma de
(puntaje x peso). Mostrar siempre la tabla completa, no solo el ganador.

## Criterios

| criterio | peso | que mide |
| --- | --- | --- |
| plataforma | 3 | encaja con donde corre el original y donde se va a usar el clon |
| integracion con el sistema | 2 | notificaciones, archivos, bandeja, servicios en segundo plano, atajos |
| offline y sincronizacion | 2 | facilidad para datos locales y sincronizar entre dispositivos |
| experiencia del usuario | 2 | cuanto conoce el usuario el stack (Kotlin/Android pesa a favor) |
| Android y PC a la vez | 2 | un solo codigo para ambas plataformas |
| capturabilidad | 1 | expone arbol de UI que `capture_*` puede leer para el diff |

## Candidatos y puntajes base

Puntajes de partida; ajustar con lo que dice el recon y explicar cada ajuste.

| candidato | plataforma | integracion | offline | experiencia | ambas | capturabilidad |
| --- | --- | --- | --- | --- | --- | --- |
| Kotlin + Jetpack Compose (Android) | 5 si el original es Android, 1 si es de escritorio | 5 | 5 | 5 | 1 | 5 |
| Kotlin Multiplatform + Compose Multiplatform | 4 | 3 | 4 | 4 | 5 | 2 |
| C# + WinUI 3 | 5 si el original es de Windows, 1 si es Android | 5 | 4 | 2 | 1 | 5 |
| C# + WPF | 4 si el original es de Windows, 1 si es Android | 4 | 4 | 2 | 1 | 5 |
| Tauri + web (TypeScript) | 4 en escritorio, 1 en Android | 3 | 3 | 3 | 2 | 4 |
| App web local (navegador) | 3 | 1 | 2 | 3 | 3 | 3 |

Notas de capturabilidad:
- Compose (Android): el arbol de semantica sale por uiautomator. Poner
  `contentDescription` y `testTag` en los elementos interactivos mejora el diff.
- Compose Multiplatform en escritorio: la accesibilidad en Windows depende de
  Java Access Bridge y suele exponer pocos nodos. De ahi el 2.
- WinUI 3 y WPF: UI Automation nativa. Poner `AutomationProperties.AutomationId`.
- Tauri: WebView2 expone el DOM accesible por UI Automation.
- Web local: capturable abierta como ventana de app (`--app=URL`). En una
  pestana normal se mezcla la UI del navegador.

## Ejemplo

Original: app de notas Android. El usuario la quiere en el telefono y en el PC.

| candidato | plataforma x3 | integracion x2 | offline x2 | experiencia x2 | ambas x2 | captura x1 | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kotlin + Compose (Android) | 15 | 10 | 10 | 10 | 2 | 5 | 52 |
| Kotlin Multiplatform | 12 | 6 | 8 | 8 | 10 | 2 | 46 |
| Tauri + web | 3 | 6 | 6 | 6 | 4 | 4 | 29 |

Recomendacion: Kotlin + Compose para Android y empezar ahi; si el PC es un
requisito duro, Kotlin Multiplatform, sabiendo que en escritorio la paridad
de UI no se podra medir con el diff de arbol.
