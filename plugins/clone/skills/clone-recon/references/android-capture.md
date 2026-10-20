# Captura Android

## Requisitos

1. **adb** (Android SDK Platform-Tools). El script lo busca en este orden:
   `--adb`, PATH, `%ANDROID_HOME%\platform-tools`,
   `%LOCALAPPDATA%\Android\Sdk\platform-tools` (donde lo deja Android
   Studio), `~/Android/Sdk/platform-tools`. Si no hay Android Studio, bajar
   Platform-Tools desde developer.android.com/tools/releases/platform-tools y
   pasar la ruta con `--adb`.
2. **Dispositivo con depuracion USB.** Ajustes > Acerca del telefono > tocar 7
   veces "Numero de compilacion". Luego Opciones de desarrollador > Depuracion
   USB. Al conectar, aceptar la huella RSA en el telefono.
3. Verificar: `adb devices` debe listar el dispositivo como `device` (no
   `unauthorized` ni `offline`).

Un emulador de Android Studio sirve igual si la app esta instalada en el.

## Uso

```
python capture_android.py --id S03@vacio --out clone/captures/original [--serial SERIAL]
```

Escribe `S03@vacio.png`, `S03@vacio.raw.xml`, `S03@vacio.tree.json` e imprime
el resumen. Exit 0 ok, 1 captura parcial, 2 error de entorno.

## Problemas conocidos

| sintoma | causa | que hacer |
| --- | --- | --- |
| exit 2 "no encuentro adb" | Platform-Tools no instalado o fuera de las rutas conocidas | instalar o pasar `--adb` |
| exit 2 "hay N dispositivos" | emulador y telefono a la vez | `--serial` con el que corresponda |
| exit 2 "no hay dispositivos" | cable solo de carga, depuracion apagada, RSA sin aceptar | revisar los 3 |
| exit 1 "uiautomator dump fallo" | animacion, video o carga continua en pantalla | pausar el video o esperar a que termine la animacion y repetir |
| exit 1 "un solo color" | la app usa FLAG_SECURE (bancos, pagos) o la pantalla esta apagada | el arbol suele salir bien; la pantalla queda sin screenshot util |
| arbol con pocos nodos | juego, Unity, Flutter sin semantica, canvas propio | `tree_quality` partial o none: la pantalla se evalua solo por features |
| exit 2 "formato de screencap no soportado" | dispositivo con formato de pixel distinto de RGBA_8888 | tomar screenshot manual y guardarlo como `<SID>.png` |

## Que guarda y que no

- Guarda la jerarquia de vistas que Android expone a accesibilidad: clases,
  textos visibles, content-desc, resource-id, bounds y flags.
- No lee memoria, archivos ni red de la app.
- Con `--no-redact` se conservan emails, telefonos y valores de campos. Solo
  usarlo con datos de prueba.
