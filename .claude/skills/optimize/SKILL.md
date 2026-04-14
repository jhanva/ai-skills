---
name: optimize
description: >
  Reglas de optimizacion de tokens y contexto que se aplican SIEMPRE.
  Gestiona effort level, delegacion a subagentes, lecturas de archivos eficientes,
  filtrado de output, compaction con foco, y seleccion de modelo.
when_to_use: >
  Siempre. Esta skill aplica a toda interaccion: codear, debuggear, revisar,
  planificar, investigar, o cualquier tarea. Es conocimiento de fondo que
  guia como trabajar de forma eficiente.
user-invocable: false
---

# Optimize — Reglas de eficiencia de tokens

Estas reglas aplican SIEMPRE, en cada accion que tomes. No son sugerencias, son restricciones operativas.

## 1. Leer archivos con precision

Las lecturas de archivos son el mayor consumidor de tokens (1,000-3,000 por archivo). Minimizalas:

- **Nunca leas archivos "por si acaso"** — solo lee lo que necesitas para la tarea actual
- **Usa Grep antes de Read** — busca el patron exacto en vez de leer archivos completos para encontrar algo
- **Usa Glob para encontrar archivos** — no leas directorios completos con `ls -R`
- **Lee con offset y limit** — si solo necesitas una funcion, lee esas lineas, no el archivo entero: `Read(file, offset=120, limit=30)`
- **No releas archivos que ya leiste** — recuerda el contenido de esta sesion

## 2. Effort level por complejidad de tarea

El extended thinking consume 10,000-50,000+ tokens de OUTPUT (los mas caros). Ajusta el esfuerzo:

| Tarea | Effort recomendado |
|---|---|
| Rename, fix typo, agregar import, formateo | low |
| Implementar funcion simple, agregar test, fix acotado | medium |
| Debugging multi-archivo, diseno, refactor complejo | high |
| Arquitectura, decisiones criticas, problemas muy dificiles | max (solo opus) |

No uses high/max para tareas que se resuelven en 2 pasos. No uses low para decisiones que requieren razonamiento profundo.

## 3. Delegar operaciones verbosas a subagentes

El output de estas operaciones inunda el contexto principal. SIEMPRE delega a un subagente:

- **Correr suites de tests completas** — el output puede ser miles de tokens. Delega y recibe solo el resumen
- **Investigar/explorar codebase** — usar subagente tipo Explore que lee multiples archivos sin inflar tu contexto
- **Leer logs largos** — un subagente puede procesar y resumir
- **Buscar en documentacion externa** — WebFetch retorna contenido masivo, mejor en subagente

Cuando delegues, especifica exactamente que necesitas de vuelta:

```
BIEN: "Corre npm test y reporta: cuantos pasan, cuantos fallan, y los nombres de los que fallan"
MAL:  "Corre npm test"  (retorna todo el output raw)
```

## 4. Filtrar output de comandos

Cuando ejecutes comandos que producen output largo, filtra ANTES de que entre al contexto:

```bash
# MAL — todo el output entra al contexto
npm test

# BIEN — solo fallos
npm test 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100

# MAL — todo el log
cat app.log

# BIEN — solo errores recientes
tail -100 app.log | grep -i error

# MAL — todo el build output
npm run build

# BIEN — solo errores
npm run build 2>&1 | grep -i -E '(error|failed)' | head -50
```

Usa el script `${CLAUDE_SKILL_DIR}/scripts/filter-output.sh` como referencia para patrones de filtrado.

## 5. Compaction inteligente

Cuando el contexto crece y necesitas compactar:

- **Usa `/compact` con foco**: `/compact focus on the auth changes and test results` — esto le dice al compresor que preservar
- **Usa `/clear` entre tareas no relacionadas** — contexto de tarea anterior es desperdicio puro
- **Antes de `/clear`, usa `/rename`** — para encontrar la sesion despues con `/resume`

## 6. Seleccion de modelo para subagentes

Cuando despachas subagentes, elige el modelo mas barato que pueda hacer el trabajo:

```
model: haiku    → leer/buscar archivos, tareas de 1-2 archivos, investigacion simple
model: sonnet   → implementacion, integracion, logica de negocio
model: opus     → arquitectura, review de calidad, debugging complejo
```

Configura en el frontmatter del subagente o pasa como parametro al Agent tool.

## 7. Prompts especificos

Cada palabra vaga genera lecturas innecesarias:

```
MAL:  "mejora este codigo"          → Claude lee todo el proyecto buscando que mejorar
BIEN: "agrega validacion de email en src/auth/login.ts linea 45"  → Claude lee 1 archivo, 1 seccion
```

## 8. CLAUDE.md limpio

- Mantener bajo 200 lineas (se carga SIEMPRE, ~9 tokens por linea)
- Mover instrucciones especificas de workflow a skills (se cargan on-demand)
- No repetir lo que esta en el codigo o git history

## Resumen de impacto

| Tecnica | Tokens ahorrados por uso |
|---|---|
| Read con offset/limit vs archivo completo | 500-2,500 |
| Effort low vs high en tarea simple | 10,000-40,000 |
| Subagente para tests vs inline | 1,000-5,000 en contexto principal |
| Filtrar output de comando | 500-3,000 |
| `/clear` entre tareas | todo el contexto acumulado |
| Modelo haiku vs opus en subagente mecanico | ~60% menos costo |
