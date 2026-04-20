---
name: humanize
description: Diagnostica y reescribe texto para que suene menos artificial y más humano en español o inglés. Úsala cuando el usuario pida explícitamente humanizar, revisar o reescribir texto con voz más natural. No la uses para edición técnica menor sin foco en tono.
---

# Humanize — Texto con voz real

## Uso en Codex

- Esta skill está pensada para invocación explícita con `$humanize`.
- Cuando aquí se indique buscar patrones, usa `rg -n`; para listar archivos, usa `rg --files` o `find`; para leer fragmentos concretos, usa `sed -n`.
- Cuando aquí se hable de subagentes, usa los agentes integrados de Codex o los definidos en `.codex/agents/`, y solo delega si el usuario pidió paralelismo o delegación.
## Por qué el texto de IA es detectable

Los detectores (GPTZero, Turnitin, Originality.ai) no buscan palabras específicas.
Miden **uniformidad estadística**:

- **Perplexity baja y constante** — la IA elige tokens de alta probabilidad, produciendo texto predecible palabra a palabra
- **Burstiness baja** — la IA produce oraciones de complejidad uniforme. Los humanos escriben en ráfagas: una oración de 5 palabras, luego una de 40, luego un fragmento
- **Estructura formulaica** — intro-cuerpo-conclusión en cada sección, siempre 3-5 puntos, transiciones predecibles

La humanización efectiva ataca estos tres ejes. Lo que NO funciona: sinónimos, typos, parafraseo, pedir "escribe como humano", subir temperature.

---

## Modos de operación

### Modo REVIEW (default)

Analiza el texto y reporta:
- Patrones de IA detectados con ubicación
- Severidad por patrón
- Sugerencias de reescritura para cada hallazgo
- Score global de "naturalidad"

**No modifica el texto.** El usuario decide qué cambiar.

### Modo REWRITE

Reescribe el texto aplicando todas las transformaciones.
Preserva el contenido y la intención; cambia la voz y estructura.

Si el prompt menciona un modo explicito, usarlo:
- `review` o sin argumento = modo review
- `rewrite` = modo rewrite

---

## FASE 1: Cargar texto

### 1.1 Resolver fuente

- Si el prompt menciona un archivo, leerlo
- Si el prompt incluye texto entre comillas, usarlo directamente
- Si el prompt no incluye texto o archivo, pedir el contenido faltante al usuario

### 1.2 Detectar idioma

Identificar si el texto es español, inglés, o mixto. Aplicar los marcadores
del idioma correspondiente. Si es mixto, aplicar ambos.

### 1.3 Detectar contexto

Identificar automáticamente (o preguntar):

| Contexto | Pistas |
|---|---|
| Documentación técnica | Archivo .md en repo, código, APIs |
| Informe/reporte | Estructura de secciones, datos, métricas |
| Ensayo/artículo | Argumentación, tesis, referencias |
| Email/mensaje | Corto, dirigido a alguien, acción esperada |
| Blog post | Título, tono informal, publicación |
| Académico | Citas, abstract, metodología |

### 1.4 Identificar audiencia y registro

| Registro | Características target |
|---|---|
| Técnico entre pares | Jerga del dominio, directo, opiniones fuertes, sin rodeos |
| Profesional formal | Preciso pero no robótico, datos concretos, sin hedging vacío |
| Académico | Argumentación rigurosa, engagement con fuentes, voz autoral |
| Casual/blog | Primera persona, humor, fragmentos, preguntas retóricas |

---

## FASE 2: Diagnóstico — detectar patrones de IA

### 2.1 Vocabulario — marcadores en español

**Tier 1 — Señales fuertes (reemplazar siempre):**

```
abordar (usado como comodín para todo), ámbito, panorama (metafórico),
multifacético, matizado (como adjetivo decorativo), apalancarse,
potenciar (como relleno), paradigma, holístico, sinergia, robusto
(fuera de contexto técnico), integral (como relleno), transversal,
vertebrar, articular (metafórico), pivotar, disruptivo, escalable
(fuera de tech), ecosistema (fuera de biología), empoderar,
visibilizar, alineado/alineamiento, impulsar (como comodín)
```

**Tier 2 — Señales moderadas (evaluar en contexto):**

```
crucial, fundamental, esencial, clave (como adjetivo repetido), significativo,
implementar (vs "hacer/meter/montar"), optimizar (como relleno), garantizar,
fomentar, propiciar, fortalecer, consolidar, innovador, estratégico,
marco (fuera de programación), en el contexto de, a nivel de
```

**Tier 3 — Frases formulaicas en español (eliminar o reestructurar):**

```
"Es importante señalar que..."
"Cabe destacar que..."
"Cabe mencionar que..."
"En la actualidad..."
"En el mundo actual..."
"En la era de..."
"Sin lugar a dudas..."
"En este sentido..."
"De esta manera..."
"Asimismo..."  (cuando se repite más de una vez)
"No obstante..."  (cuando se repite)
"Por ende..."
"En definitiva..."
"A modo de conclusión..."
"En resumidas cuentas..."
"En primer lugar... En segundo lugar... En tercer lugar..."
"Por un lado... por otro lado..."
"Dicho lo anterior..."
"Es menester..."
"Resulta pertinente..."
"Es preciso mencionar..."
"Huelga decir que..."
"Es fundamental tener en cuenta que..."
"En lo que respecta a..."
"Con respecto a lo anterior..."
"En este orden de ideas..."
"Lo anteriormente expuesto..."
```

### 2.2 Marcadores en inglés (para textos en inglés o mixtos)

**Tier 1:**
```
delve, tapestry, landscape (metafórico), multifaceted, nuanced (decorativo),
pivotal, paramount, cornerstone, foster, leverage (verbo), streamline,
underscore, intricate, realm, embark, navigate (metafórico), spearhead,
groundbreaking, transformative, game-changing, cutting-edge, holistic,
synergy, robust (fuera de tech), seamless, comprehensive (relleno),
utilize, facilitate
```

**Tier 3 — Frases formulaicas en inglés:**
```
"It's important to note that..."
"It's worth mentioning that..."
"In today's rapidly evolving..."
"In conclusion..."
"Overall, ..."
"Firstly, ... Secondly, ... Thirdly, ..."
"Whether you're a... or a..."
"Let's dive in..."
"Without further ado..."
```

### 2.3 Patrones gramaticales de IA en español

La IA en español tiene vicios gramaticales específicos que los humanos nativos no cometen:

**Gerundio abusivo:**
```
ANTES (IA): "La empresa está implementando soluciones, mejorando procesos
y fortaleciendo capacidades, logrando así resultados significativos."

DESPUÉS: "La empresa implementó tres cosas: soluciones nuevas, procesos
más ágiles y un equipo con más autonomía. Funcionó."
```
El encadenamiento de gerundios es marca registrada de IA en español.

**Nominalización excesiva:**
```
ANTES (IA): "La implementación de la optimización del proceso de
digitalización requiere la consideración de múltiples factores."

DESPUÉS: "Para digitalizar bien, hay que pensar en varias cosas a la vez."
```
La IA convierte verbos en sustantivos abstractos. Los humanos usan verbos directos.

**Abuso de "el cual / la cual / los cuales":**
```
ANTES (IA): "El sistema, el cual fue diseñado para abordar las
necesidades de los usuarios, los cuales requieren soluciones integrales..."

DESPUÉS: "El sistema se diseñó para lo que los usuarios realmente necesitan."
```
Los humanos usan "que" casi siempre. "El cual" es para desambiguar, no para decorar.

**Voz pasiva con "se" en exceso:**
```
ANTES (IA): "Se implementó una solución que se diseñó para que se
pudieran realizar las tareas que se habían identificado."

DESPUÉS: "Diseñamos una solución para las tareas que encontramos pendientes."
```

**Conectores apilados:**
```
ANTES (IA): "Asimismo, es importante destacar que, no obstante, en este
sentido, cabe señalar que por ende resulta fundamental..."

DESPUÉS: "Pero hay un problema."
```

### 2.4 Estructura — patrones formulaicos

| Patrón | Señal de IA | Qué buscar |
|---|---|---|
| Párrafos uniformes | Todos entre 60-120 palabras | Medir longitud de cada párrafo |
| Listas simétricas | Siempre 3 o 5 items, estructura paralela perfecta | Contar items, verificar paralelismo |
| Restamiento del tema | Primer párrafo repite la pregunta o el título | Leer apertura |
| Transiciones predecibles | "Asimismo", "No obstante", "En este sentido" en cada párrafo | Contar transiciones formulaicas |
| Cierre tipo resumen | Último párrafo empieza con "En conclusión", "En definitiva" | Leer cierre |
| Headers genéricos | "Introducción", "Desarrollo", "Conclusiones" | Evaluar headers |
| Estructura sándwich | Cada sección: contexto + puntos + cierre parcial | Evaluar estructura |

### 2.5 Ritmo — uniformidad de oraciones

Medir longitud de cada oración (en palabras):

```
Perfil típico de IA:   [15, 18, 14, 16, 19, 15, 17]  → varianza baja
Perfil típico humano:  [4, 28, 12, 3, 35, 8, 22, 6]  → varianza alta, ráfagas
```

**Métrica:** Si el rango (max - min) de longitud de oraciones en un párrafo es <15 palabras, es señal de IA.

### 2.6 Tono — neutralidad artificial

| Patrón | Señal de IA |
|---|---|
| Hedging excesivo | "podría", "eventualmente", "en cierta medida", "de alguna manera" |
| Balance forzado | Siempre presenta "ambos lados" sin tomar posición |
| Entusiasmo genérico | "esta poderosa herramienta", "increíblemente útil" sin evidencia |
| Ausencia de persona | Sin "yo", "nosotros", sin anécdota, sin opinión directa |
| Diplomacia extrema | Nunca dice "esto está mal" o "esto no funciona" |
| Formalidad artificial | "Se procedió a realizar" en vez de "hicimos" |

---

## FASE 3: Transformación (modo rewrite) / Sugerencias (modo review)

Lee `references/rewrite-patterns.md` solo cuando vayas a reescribir o a emitir el diagnostico final.

### Reglas base

1. Romper ritmo: variar longitud de oraciones y parrafos
2. Reemplazar abstraccion por detalle concreto cuando exista
3. Eliminar hedging y formalidad artificial que no aportan significado
4. Tomar posicion y mostrar razonamiento, no solo balance vacio
5. Reescribir vicios gramaticales de IA a voz activa y verbos directos

## FASE 4: Ajustes por tipo de documento

Usa `references/rewrite-patterns.md` para elegir el registro correcto segun sea documentacion tecnica, informe, ensayo, blog, email o academico.

- documentacion tecnica: directa, explicativa, con tradeoffs reales
- informe: abre con hallazgo y recomendacion
- ensayo/blog: mas voz, posicion y ritmo
- email: breve y accionable
- academico: formal sin sonar mecanico

## FASE 5: Reporte (modo review) / Verificación (modo rewrite)

### Modo review

Entregar:
- score de naturalidad
- idioma detectado
- hallazgos por vocabulario, gramatica, estructura, ritmo y tono
- recomendaciones priorizadas por impacto

### Modo rewrite

Verificar:
- sin marcadores fuertes de IA
- sin nominalizaciones o gerundios encadenados innecesarios
- ritmo mas variado
- registro consistente
- hechos preservados

Si hace falta un ejemplo concreto de reescritura o el template completo del diagnostico, cargarlo desde `references/rewrite-patterns.md`.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
