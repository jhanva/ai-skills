---
name: room-audit
description: Audita bases de datos Room para detectar migraciones riesgosas, esquemas sin exportar, converters frágiles e índices faltantes. Úsala cuando el usuario pida explícitamente revisar Room o migraciones Android. No la uses para bases de datos no Room.
---

# Room Audit — Auditoria de seguridad de datos

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$room-audit`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Ley de hierro: READ-ONLY

**PROHIBIDO modificar archivos.** Solo reportar hallazgos inline.

## Resolver target

1. Si el prompt incluye una ruta, usarla como target
2. Si el prompt no especifica ruta, usar el directorio actual
3. Validar que contiene Room (`Busca con `rg -n`: "androidx.room"`)

---

## FASE 1: Reconocimiento de base de datos

### 1.1 Encontrar componentes Room

```
# Database class
Busca con `rg -n`: "@Database"

# Entities
Busca con `rg -n`: "@Entity"

# DAOs
Busca con `rg -n`: "@Dao"

# Migrations
Busca con `rg -n`: "Migration("

# Type Converters
Busca con `rg -n`: "@TypeConverter"
```

Construir mapa:
- Que tablas existen y su version actual
- Cuantas migraciones hay definidas
- Que DAOs acceden a que tablas

---

## FASE 2: Schema Export

### Check 1 — exportSchema

Leer la clase `@Database`:

```kotlin
@Database(entities = [...], version = N, exportSchema = false)  // PROBLEMA
@Database(entities = [...], version = N, exportSchema = true)   // CORRECTO
```

Si `exportSchema = false`:
- Reportar como CRITICO
- Sin schema export, no hay forma automatizada de verificar que las migraciones son correctas
- Room genera JSON schemas en `schemas/` que sirven como snapshot para testing

Verificar tambien:
- En `build.gradle.kts`, buscar `room { schemaDirectory(...) }` o `kapt { arguments { arg("room.schemaLocation", ...) } }`
- Si exportSchema = true pero no hay schemaDirectory configurado, los schemas no se guardan

---

## FASE 3: Migration Safety

### Check 2 — Migraciones sin tests

Para cada `Migration(fromVersion, toVersion)` encontrada:

1. Buscar en archivos de test un test que la referencie:
   ```
   Busca con `rg -n`: "MigrationTestHelper" | "MIGRATION_X_Y" | "migration.*X.*Y"
   ```
2. Si no hay test, reportar como CRITICO
   - Migraciones sin test pueden perder datos silenciosamente en produccion
   - El test debe usar `MigrationTestHelper` de `androidx.room:room-testing`

### Check 3 — Migraciones con SQL peligroso

Leer el SQL de cada migracion y verificar:

- `DROP TABLE` sin `CREATE TABLE` + `INSERT INTO ... SELECT` → perdida de datos
- `ALTER TABLE ... RENAME` → puede romper FKs en SQLite < 3.25
- Falta `NOT NULL` con `DEFAULT` en columnas nuevas → crash en upgrade
- `CREATE TABLE` sin copiar datos de tabla anterior → perdida de datos

Para cada pattern peligroso, reportar como CRITICO con el SQL exacto.

### Check 4 — Auto-migration vs manual

Si el proyecto usa Room auto-migrations (`autoMigrations = [AutoMigration(from=X, to=Y)]`):
- Verificar que hay spec classes para cambios que requieren `@DeleteColumn`, `@RenameColumn`, etc.
- Sin spec, cambios destructivos causan crash en runtime

---

## FASE 4: Type Converters

### Check 5 — Converters fragiles

Buscar `@TypeConverter` y analizar:

**Patrones peligrosos:**

```kotlin
// Delimitador que puede aparecer en datos
fun fromList(value: String): List<String> = value.split("||")  // PELIGRO
fun fromList(value: String): List<String> = value.split(",")   // PELIGRO

// Deserializacion sin error handling
fun fromJson(value: String): MyType = Gson().fromJson(value, MyType::class.java)  // PELIGRO si JSON corrupto
```

**Patrones seguros:**

```kotlin
// JSON con error handling
fun fromJson(value: String): MyType? = try { Json.decodeFromString(value) } catch (e: Exception) { null }

// Enum con fallback
fun fromString(value: String): Status = try { Status.valueOf(value) } catch (e: Exception) { Status.UNKNOWN }
```

Para cada converter fragil, reportar como IMPORTANTE con sugerencia de reemplazo.

---

## FASE 5: Indices y Performance

### Check 6 — Indices faltantes

Para cada `@Dao`, leer las queries:

```kotlin
@Query("SELECT * FROM images WHERE folderId = :folderId")
```

Verificar que las columnas en WHERE, JOIN ON, y ORDER BY tengan indice:
- Definido en `@Entity(indices = [Index("folderId")])`
- O como parte de `@ForeignKey`
- O como `@ColumnInfo(index = true)` (deprecated pero funcional)

Columnas sin indice usadas en queries frecuentes → reportar como IMPORTANTE.

### Check 7 — FK cascades

Para cada `@ForeignKey` definida:
- Verificar `onDelete` esta definido (sin el, default es `NO ACTION` → crash si se borra el parent)
- Si `onDelete = CASCADE`, verificar que es intencional (puede borrar datos en cadena)
- Si `onDelete = SET_NULL`, verificar que la columna es nullable

---

## FASE 6: Transaction Boundaries

### Check 8 — Operaciones multi-tabla sin @Transaction

Buscar metodos en DAOs o repositories que:
1. Hacen multiples operaciones de escritura en la misma funcion
2. Leen datos que dependen de consistencia entre tablas

```kotlin
// PELIGRO — sin @Transaction
suspend fun moveImage(imageId: Long, newFolderId: Long) {
    deleteFromFolder(imageId)      // Si crashea aqui...
    insertIntoFolder(imageId, newFolderId)  // ...imagen perdida
}

// CORRECTO
@Transaction
suspend fun moveImage(imageId: Long, newFolderId: Long) { ... }
```

Para operaciones multi-tabla sin `@Transaction`, reportar como IMPORTANTE.

---

## FASE 7: Reporte

```markdown
## Auditoria de Room database

### CRITICO (riesgo de perdida de datos)
- `data/db/AppDatabase.kt:5` — exportSchema = false
  Impacto: no hay schema snapshots para validar migraciones
  Fix: cambiar a exportSchema = true, agregar room { schemaDirectory("$projectDir/schemas") }

- `data/db/AppDatabase.kt:12` — MIGRATION_2_3 sin test
  Impacto: migracion puede perder datos silenciosamente en produccion
  Fix: agregar test con MigrationTestHelper

### IMPORTANTE (bug latente)
- `data/db/converter/TagConverter.kt:8` — split("||") como delimitador
  Impacto: tags que contengan "||" rompen la deserializacion
  Fix: usar JSON serialization (kotlinx.serialization)

### MENOR (mejora recomendada)
- `data/db/entity/ImageEntity.kt:15` — columna `folderId` sin indice
  Impacto: queries con WHERE folderId son full table scan
  Fix: agregar @Index("folderId") en @Entity

### Resumen
| Severidad | Cantidad |
|---|---|
| Critico | N |
| Importante | N |
| Menor | N |

Database version: N | Tablas: N | DAOs: N | Migraciones: N
Tests de migracion encontrados: N/N
```

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
