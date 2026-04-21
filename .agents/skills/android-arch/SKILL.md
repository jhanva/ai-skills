---
name: android-arch
description: Audita boundaries de Clean Architecture en proyectos Android/Kotlin. Úsala cuando el usuario pida explícitamente revisar arquitectura, dependencias entre capas, código muerto o DI en Android. No la uses para implementación general ni para proyectos que no sean Android/Kotlin.
---

# Android Arch — Validacion de boundaries de Clean Architecture

## Uso en Codex

- Esta skill esta pensada para invocacion explicita con `$android-arch`.
- Trabaja con lecturas puntuales: `rg -n` para buscar, `rg --files` o `find` para listar, y `sed -n` para leer solo el fragmento necesario.
- Haz la auditoria en la sesion principal. Solo delega si el usuario pidio paralelismo o delegacion.
- Si falta contexto menor, audita el target actual y declara cualquier limitacion.
## Ley de hierro: READ-ONLY

**PROHIBIDO modificar archivos.** Solo reportar hallazgos inline.

## Resolver target

1. Si el prompt incluye una ruta, usarla como target
2. Si el prompt no especifica ruta, usar el directorio actual
3. Validar que existe y contiene `build.gradle` o `build.gradle.kts`

---

## FASE 1: Reconocimiento

### 1.1 Detectar estructura del proyecto

```bash
# Single module o multi-module?
find TARGET -name "build.gradle.kts" -o -name "build.gradle" | head -20
```

Identificar:
- Modulos Gradle (app, domain, data, feature:*, core:*)
- Paquetes dentro de cada modulo (domain/, data/, presentation/, di/, util/)
- Si no hay modulos separados, buscar paquetes por convencion

### 1.2 Mapear capas

Construir mapa de capas del proyecto:

| Capa | Donde buscar |
|---|---|
| Domain | Modulo `domain/` o paquete `*/domain/**` |
| Data | Modulo `data*/` o paquete `*/data/**` |
| Presentation | Modulo `feature*/` o `app/` o paquete `*/presentation/**`, `*/ui/**` |
| DI | Paquete `*/di/**` o `*/module/**` |

---

## FASE 2: Domain Purity — imports prohibidos

Escanear TODOS los archivos `.kt` en la capa domain:

```
# Imports prohibidos en domain layer
android\..*          (excepto android.os.Parcelable si se usa para modelos)
androidx\..*
java\.io\.File
java\.net\.URL
retrofit2\..*
okhttp3\..*
room\..*
```

**Imports permitidos en domain:**
- `kotlin.*`, `kotlinx.coroutines.*`, `kotlinx.coroutines.flow.*`
- `javax.inject.*` (Hilt/Dagger inject)
- Tipos propios del domain layer

Para cada violacion, reportar archivo:linea y el import concreto.

**Caso especial — `android.net.Uri`:** Es la violacion mas comun. Reportar como CRITICO con sugerencia de reemplazar por `String` en el domain model y convertir en la capa data/presentation.

---

## FASE 3: Dead Code Detection

### 3.1 Clases no referenciadas

Para cada archivo `.kt` en el proyecto:

1. Extraer el nombre de la clase/object/interface principal
2. Buscar referencias a ese nombre en OTROS archivos (excluyendo imports del mismo paquete)
3. Excluir de la busqueda:
   - `@Entity`, `@Dao`, `@Database` (Room las usa via reflection)
   - `@HiltWorker`, `@AndroidEntryPoint` (Hilt las instancia)
   - `MainActivity`, `Application` (entry points Android)
   - Test files
4. Si una clase no tiene referencias externas y no es un entry point, reportar como dead code

### 3.2 DI bindings sin consumidores

Para cada `@Provides` o `@Binds` en modulos Hilt:

1. Identificar el tipo que retorna
2. Buscar `@Inject` constructors o parametros que consuman ese tipo
3. Si no hay consumidor, reportar como binding huerfano

---

## FASE 4: Module Dependencies (solo multi-module)

Si el proyecto tiene multiples modulos Gradle:

1. Leer `build.gradle.kts` de cada modulo
2. Extraer `implementation(project(":modulo"))` dependencies
3. Verificar reglas:
   - `domain` NO debe depender de `data`, `app`, ni `feature:*`
   - `data` NO debe depender de `presentation`, `app`, ni `feature:*`
   - `feature:*` NO debe depender de otros `feature:*` (salvo shared/common)
   - `core:model` NO debe depender de nada excepto Kotlin stdlib

Para cada violacion, reportar la dependencia concreta y la regla que rompe.

---

## FASE 5: Reporte

```markdown
## Auditoria de arquitectura Android

### CRITICO (viola boundaries fundamentales)
- `domain/model/ImageItem.kt:3` — `import android.net.Uri` en domain layer
  Impacto: domain layer depende de Android framework, impide testing puro JVM
  Fix: cambiar `uri: Uri` por `uri: String`, convertir en data/presentation

### IMPORTANTE (tech debt significativo)
- `util/hash/DifferenceHashCalculator.kt` — clase nunca referenciada (dead code)
  Impacto: mantenimiento innecesario, confusion para nuevos contribuidores
  Fix: eliminar archivo

### MENOR (mejora recomendada)
- `di/AppModule.kt:120` — modulo DI con 15+ providers, considerar dividir
  Fix: separar en NetworkModule, RepositoryModule, UseCaseModule

### Resumen
| Severidad | Cantidad |
|---|---|
| Critico | N |
| Importante | N |
| Menor | N |

Capas detectadas: [domain, data, presentation, di]
Modulos: [N modulos Gradle]
Archivos escaneados: N
```

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
