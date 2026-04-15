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

### Regla 1 — Ritmo roto (MAYOR IMPACTO)

La intervención con más retorno. Reescribir variando longitud de oraciones dramáticamente:

```
ANTES (IA):
"La transformación digital de las organizaciones contemporáneas requiere
una consideración cuidadosa de múltiples factores interrelacionados.
Estos factores incluyen las implicaciones tecnológicas, las consideraciones
de experiencia de usuario y las preocupaciones de sostenibilidad a largo
plazo. Cada uno de estos aspectos desempeña un papel fundamental en la
determinación del éxito general del proyecto."

DESPUÉS (humano):
"Digitalizar una empresa es complicado. No por la tecnología — eso es
lo fácil. Lo difícil es que la gente lo use, que no se caiga el primer
mes, y que alguien lo mantenga después. Tres frentes que rara vez se
atienden juntos. Y ahí es donde se pudre todo."
```

**Reglas concretas:**
- Al menos una oración de ≤6 palabras por párrafo
- Al menos una oración de ≥25 palabras por párrafo
- Permitir fragmentos: "Exacto." / "Ni de cerca." / "Cero."
- Empezar oraciones con "Y", "Pero", "Porque", "O sea"
- Usar oraciones de una sola palabra como párrafo cuando tenga impacto

### Regla 2 — Especificidad concreta

Reemplazar generalidades con detalles concretos:

```
ANTES: "Esto mejoró significativamente el rendimiento."
DESPUÉS: "El query bajó de 3.2 segundos a 180 milisegundos."

ANTES: "Muchas organizaciones enfrentan este desafío."
DESPUÉS: "Nos pasó en el sprint de enero — perdimos dos semanas."

ANTES: "Los resultados fueron impresionantes."
DESPUÉS: "42% más de conversión. No me lo esperaba."

ANTES: "Se requiere una inversión considerable."
DESPUÉS: "Son $40,000 dólares y tres meses de un equipo de cuatro personas."
```

Si no hay datos concretos disponibles, preguntar al usuario o marcar con `[DATO CONCRETO AQUÍ]`.

### Regla 3 — Eliminar hedging vacío

```
ANTES: "Es importante señalar que este enfoque podría potencialmente ayudar..."
DESPUÉS: "Este enfoque ayuda cuando..."

ANTES: "Se podría argumentar que la implementación resulta de cierta complejidad."
DESPUÉS: "La implementación es compleja."

ANTES: "Existen diversos factores que deberían tomarse en consideración."
DESPUÉS: "Tres cosas a considerar:"

ANTES: "En cierta medida, los resultados podrían sugerir una tendencia."
DESPUÉS: "Los resultados muestran una tendencia clara."
```

**Test:** Si eliminar el hedge no cambia el significado, eliminarlo.

### Regla 4 — Voz y posición

```
ANTES: "Existen tanto ventajas como desventajas en este enfoque."
DESPUÉS: "Este enfoque resuelve X bien pero rompe Y. Para nuestro caso, vale la pena."

ANTES: "Se podría considerar el uso de microservicios para este propósito."
DESPUÉS: "Usá microservicios. Un monolito no aguanta este nivel de concurrencia."

ANTES: "Es fundamental analizar las diferentes perspectivas antes de tomar una decisión."
DESPUÉS: "Mi recomendación: ir con la opción B. La A suena bien en papel pero en la práctica se cae."
```

**Reglas:**
- Tomar una posición. Si hay matiz, expresarlo como "X, pero ojo con Y"
- Usar primera persona cuando el contexto lo permite
- Incluir el razonamiento, no solo la conclusión
- Usar lenguaje directo: "creo que", "me parece", "en mi experiencia"

### Regla 5 — Estructura imperfecta

```
ANTES:
## Introducción
[párrafo uniforme que repite el título]
## Desarrollo
### Primer aspecto
[punto balanceado]
### Segundo aspecto
[punto balanceado]
### Tercer aspecto
[punto balanceado]
## Conclusiones
[resumen de todo lo anterior]

DESPUÉS:
## El problema real
[dos oraciones que van al grano]

## Lo que probamos
[párrafo largo con el detalle]
[oración suelta que cierra]

## Qué funcionó y qué no
[párrafo corto con lo que sí]
[párrafo más largo con lo que no — porque los fracasos merecen más explicación]
```

**Reglas:**
- No todos los párrafos necesitan topic sentence
- Variar longitud de párrafos (1 oración, 5 oraciones, 3 oraciones)
- Eliminar secciones de "Introducción" y "Conclusiones" explícitas
- Headers que digan algo específico, no genérico
- Permitir que una sección termine sin cerrar — la siguiente puede retomar

### Regla 6 — Interrupciones y asides

```
ANTES: "La capa de caché proporciona mejoras significativas de rendimiento
al almacenar datos de acceso frecuente en memoria."

DESPUÉS: "El caché mejora performance — y mucho, hablamos de 10x en
lecturas calientes — pero ojo: un caché mal invalidado es peor que no
tener caché."
```

- Paréntesis: (esto es clave)
- Rayas: — como interrupción del pensamiento
- Auto-corrección: "Bueno, en realidad no es tan simple."
- Digresión breve que agrega contexto
- Preguntas retóricas: "¿Y qué pasó? Lo que siempre pasa."

### Regla 7 — Vocabulario natural del español

Reemplazar vocabulario artificial por cómo habla la gente realmente:

```
ANTES: "Se procedió a implementar una solución integral para abordar la problemática."
DESPUÉS: "Armamos una solución para el problema."

ANTES: "Es menester articular los diferentes ámbitos para potenciar los resultados."
DESPUÉS: "Hay que conectar las áreas para que funcione mejor."

ANTES: "La optimización de los procesos de gestión resulta fundamental."
DESPUÉS: "Necesitamos que los procesos funcionen más rápido."

ANTES: "Se debe fomentar un ecosistema que propicie la innovación disruptiva."
DESPUÉS: "Hay que crear un ambiente donde la gente pueda probar ideas nuevas."
```

**Coloquialismos naturales del español** (usar según registro):
- "O sea" — para aclarar
- "La verdad es que" — para introducir opinión honesta
- "El tema es que" / "La cosa es que" — para ir al punto
- "Ojo con" — para advertencias
- "Ni hablar de" — para enfatizar
- "Dale" / "Listo" — para transiciones informales
- "Ponele que" — para hipotéticos (informal)

### Regla 8 — Deshacer vicios gramaticales de IA

**Gerundios encadenados → verbos conjugados:**
```
ANTES: "Implementando mejoras, optimizando recursos y fortaleciendo capacidades."
DESPUÉS: "Mejoramos tres cosas: el código, los recursos y la capacidad del equipo."
```

**Nominalizaciones → verbos directos:**
```
ANTES: "La realización de la evaluación de la implementación..."
DESPUÉS: "Cuando evaluamos cómo se implementó..."
```

**"El cual" decorativo → "que":**
```
ANTES: "El sistema, el cual fue diseñado para los usuarios, los cuales necesitan..."
DESPUÉS: "El sistema que diseñamos para lo que los usuarios necesitan..."
```

**Pasiva con "se" excesiva → voz activa:**
```
ANTES: "Se realizó un análisis que se diseñó para que se identificaran los problemas."
DESPUÉS: "Analizamos el sistema y encontramos los problemas."
```

---

## FASE 4: Ajustes por tipo de documento

### Documentación técnica

- Registro: directo, imperativo, sin adornos
- Permitido: fragmentos, opiniones sobre tradeoffs, jerga técnica, "nosotros"
- Prohibido: entusiasmo genérico ("esta poderosa herramienta"), hedging, nominalizaciones
- Especial: incluir el "por qué" además del "cómo", usar nombres reales de funciones/APIs
- En español técnico: mezclar términos en inglés cuando es lo natural ("deploy", "merge", "endpoint")

### Informe/reporte

- Registro: profesional pero con voz
- Permitido: primera persona del plural, recomendaciones directas, datos concretos
- Prohibido: balance forzado, "por un lado / por otro lado" sin posición, generalidades
- Especial: abrir con el hallazgo principal, no con contexto. Contexto después
- En español: evitar "se procedió a realizar", usar "hicimos", "encontramos", "recomendamos"

### Ensayo/artículo

- Registro: argumentativo con personalidad
- Permitido: primera persona, posiciones fuertes, preguntas retóricas, anécdotas
- Prohibido: "en la actualidad", listas de pros y contras sin posición, "cabe destacar"
- Especial: engagement real con fuentes (no solo "Según X..."), contraargumentos que se responden
- En español: permitir oraciones largas con subordinadas (es natural del español), pero variar con cortas

### Blog post

- Registro: conversacional, personalidad marcada
- Permitido: humor, anécdotas, fragmentos, una línea como párrafo, preguntas al lector
- Prohibido: TODA frase formulaica del Tier 3, estructura de libro de texto
- Especial: abrir con una historia o una afirmación provocadora, no con definición
- En español: usar coloquialismos, "o sea", "la verdad", tuteo o voseo según la audiencia

### Email/mensaje

- Registro: directo, breve, accionable
- Permitido: frases cortas, ir al grano en primera línea, informalidad
- Prohibido: párrafos de >3 oraciones, hedging, formalidad innecesaria
- Especial: la acción esperada debe ser obvia sin tener que buscarla
- En español: "Hola [nombre]," no "Estimado/a señor/a". Cerrar con "Gracias" o "Saludos", no con "Quedo a su disposición para cualquier consulta que pudiera surgir"

### Académico

- Registro: formal pero con voz autoral, no robótico
- Permitido: primera persona del plural académico, posiciones argumentadas, complejidad sintáctica
- Prohibido: "es menester", "huelga decir", "resulta pertinente" (arcaísmos que la IA sobreusa), hedging excesivo
- Especial: citar con engagement ("Como demuestra García (2024), y contrario a lo que sostiene López..."), no solo listar fuentes
- En español: la prosa académica en español es naturalmente más elaborada que en inglés — oraciones más largas están bien, pero deben tener propósito, no relleno

---

## FASE 5: Reporte (modo review) / Verificación (modo rewrite)

### Modo review — output

```markdown
## Diagnóstico de naturalidad

### Score: N/10 (1 = claramente IA, 10 = indistinguible de humano)

### Idioma detectado: [español|inglés|mixto]

### Hallazgos

**Vocabulario (N marcadores encontrados)**
- Línea 12: "abordar" → reemplazar por verbo específico: "resolver", "atacar", "trabajar en"
- Línea 34: "Es importante señalar que" → eliminar, ir directo al punto
- Línea 45: "ámbito" → reemplazar: "área", "campo", "tema"

**Gramática IA** (solo español)
- Línea 20: gerundios encadenados (3 seguidos) → conjugar verbos
- Línea 38: nominalización: "la realización del análisis" → "cuando analizamos"
- Línea 55: "el cual" decorativo → usar "que"

**Estructura**
- Párrafos 2-5 tienen longitud casi idéntica (82, 78, 85, 80 palabras)
- 3 secciones siguen patrón intro-3puntos-conclusión
- Headers genéricos: "Introducción", "Desarrollo", "Conclusiones"

**Ritmo**
- Rango de longitud de oraciones: 12-19 palabras (muy bajo, señal fuerte de IA)
- 0 oraciones de <6 palabras, 0 de >25 palabras

**Tono**
- 4 instancias de hedging sin contenido
- 0 opiniones directas o posiciones claras
- 0 uso de primera persona
- Formalidad artificial en líneas 15, 28, 42

### Recomendaciones prioritarias
1. [mayor impacto] Romper ritmo: agregar oraciones cortas y largas
2. Eliminar N frases formulaicas (Tier 3)
3. Deshacer N vicios gramaticales (gerundios, nominalizaciones)
4. Reemplazar N marcadores de vocabulario Tier 1
5. Tomar posición en sección N en vez de presentar "ambos lados"
```

### Modo rewrite — verificación post

Después de reescribir, verificar:
- [ ] Ningún marcador Tier 1 presente
- [ ] Ningún gerundio encadenado (>2 seguidos)
- [ ] Ninguna nominalización innecesaria
- [ ] Rango de longitud de oraciones > 20 palabras por párrafo
- [ ] Al menos 1 párrafo de ≤2 oraciones y 1 de ≥4
- [ ] Hedging reducido >50% vs original
- [ ] Sin frases formulaicas Tier 3
- [ ] Contenido factual preservado (nada inventado ni omitido)
- [ ] Registro consistente con el tipo de documento
- [ ] Tildes y ortografía correctas en español

Si alguna verificación falla, ajustar antes de entregar.

## Entrada esperada

Toma del prompt del usuario cualquier ruta, modo o contexto adicional que acompañe a la invocacion de la skill.
