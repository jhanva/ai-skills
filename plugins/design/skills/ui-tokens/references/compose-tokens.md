# Tokens para Jetpack Compose

Los valores (`#RRGGBB`, tamanos, escala) salen de `MASTER.md`; aqui solo la estructura.

## Color.kt

```kotlin
package <paquete>.ui.theme

import androidx.compose.ui.graphics.Color

// Tokens crudos: un nombre por valor de MASTER.md. Los componentes NO importan esto.
internal val Primary = Color(0xFF2563EB)
internal val Secondary = Color(0xFF475569)
internal val Accent = Color(0xFFF59E0B)
internal val BackgroundLight = Color(0xFFFFFFFF)
internal val BackgroundDark = Color(0xFF0F172A)
internal val TextOnLight = Color(0xFF0F172A)
internal val TextOnDark = Color(0xFFE2E8F0)
internal val Success = Color(0xFF15803D)
internal val Warning = Color(0xFFB45309)
internal val Error = Color(0xFFB91C1C)
```

## Theme.kt

```kotlin
private val LightColors = lightColorScheme(
    primary = Primary,
    onPrimary = Color.White,
    secondary = Secondary,
    tertiary = Accent,
    background = BackgroundLight,
    onBackground = TextOnLight,
    surface = BackgroundLight,
    onSurface = TextOnLight,
    error = Error,
    onError = Color.White,
)

private val DarkColors = darkColorScheme(
    primary = Primary,          // o la variante clara indicada en MASTER.md para texto
    onPrimary = Color.White,
    secondary = Secondary,
    tertiary = Accent,
    background = BackgroundDark,
    onBackground = TextOnDark,
    surface = BackgroundDark,
    onSurface = TextOnDark,
    error = Error,
    onError = Color.White,
)

@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = AppTypography,
        shapes = AppShapes,
        content = content,
    )
}
```

`dynamicColor` queda fuera salvo autorizacion en `MASTER.md`: el color dinamico invalida el
contraste que se valido al elegir la paleta.

## Type.kt

```kotlin
val AppTypography = Typography(
    displayLarge = TextStyle(fontFamily = Titulos, fontWeight = FontWeight.Bold, fontSize = 40.sp, lineHeight = 48.sp),
    titleLarge   = TextStyle(fontFamily = Titulos, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleMedium  = TextStyle(fontFamily = Titulos, fontWeight = FontWeight.SemiBold, fontSize = 18.sp, lineHeight = 24.sp),
    bodyLarge    = TextStyle(fontFamily = Cuerpo, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium   = TextStyle(fontFamily = Cuerpo, fontSize = 14.sp, lineHeight = 20.sp),
    labelLarge   = TextStyle(fontFamily = Cuerpo, fontWeight = FontWeight.Medium, fontSize = 14.sp, lineHeight = 20.sp),
    labelSmall   = TextStyle(fontFamily = Cuerpo, fontSize = 12.sp, lineHeight = 16.sp),
)
```

Base y line-height de `MASTER.md` (Tipografia). Nada por debajo de 12.sp. Para cifras
tabulares: `fontFeatureSettings = "tnum"`.

## Spacing.kt y Shape.kt

```kotlin
object Spacing {
    val xs = 4.dp; val sm = 8.dp; val md = 16.dp; val lg = 24.dp; val xl = 32.dp; val xxl = 48.dp
}

val AppShapes = Shapes(
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
)
```

Los valores de `Spacing` son exactamente la escala de la seccion Espaciado de `MASTER.md`.

## Test de contraste (RED primero)

Test JVM puro, sin emulador, en `src/test/.../ThemeContrastTest.kt`:

```kotlin
class ThemeContrastTest {
    private fun luminance(c: Long): Double {
        fun ch(v: Long): Double { val s = v / 255.0; return if (s <= 0.03928) s / 12.92 else Math.pow((s + 0.055) / 1.055, 2.4) }
        return 0.2126 * ch((c shr 16) and 0xFF) + 0.7152 * ch((c shr 8) and 0xFF) + 0.0722 * ch(c and 0xFF)
    }
    private fun ratio(a: Long, b: Long): Double {
        val (hi, lo) = listOf(luminance(a), luminance(b)).sortedDescending()
        return (hi + 0.05) / (lo + 0.05)
    }

    @Test fun textoSobreFondoClaroCumpleAA() = assertTrue(ratio(0x0F172A, 0xFFFFFF) >= 4.5)
    @Test fun textoSobreFondoOscuroCumpleAA() = assertTrue(ratio(0xE2E8F0, 0x0F172A) >= 4.5)
    @Test fun onPrimarySobrePrimaryCumpleAA() = assertTrue(ratio(0xFFFFFF, 0x2563EB) >= 4.5)
}
```

Los hex del test son los de `MASTER.md`. Falla en RED porque `Color.kt` no existe todavia
solo si el test importa los tokens; alternativa: comparar contra los valores de `Color.kt`
leyendo `Primary.value`, que exige que el archivo exista.

## Previews obligatorias

Cada pantalla que consuma el tema lleva `@Preview` claro, oscuro (`uiMode = UI_MODE_NIGHT_YES`)
y `fontScale = 1.5f`.
