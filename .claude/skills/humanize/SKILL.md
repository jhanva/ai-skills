---
name: humanize
description: >
  Humaniza texto generado por IA. Diagnostica patrones detectables (vocabulario,
  estructura, ritmo, tono) y los transforma para producir texto con voz natural.
  Dos modos: review (diagnostico) y rewrite (transformacion).
when_to_use: >
  Cuando el usuario dice "humanizar", "humanize", "suena a IA", "suena artificial",
  "suena falso", "hazlo mas natural", "reescribir como humano", "quitar tono de IA",
  o pide revisar/mejorar texto que parece generado por IA.
argument-hint: "[review|rewrite] [archivo o texto]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - Agent
  - Bash(wc *)
---

# Humanize — Texto con voz real

## Por que el texto de IA es detectable

Los detectores (GPTZero, Turnitin, Originality.ai) no buscan palabras especificas.
Miden **uniformidad estadistica**:

- **Perplexity baja y constante** — la IA elige tokens de alta probabilidad, produciendo texto predecible palabra a palabra
- **Burstiness baja** — la IA produce oraciones de complejidad uniforme. Los humanos escriben en rafagas: una oracion de 5 palabras, luego una de 40, luego un fragmento
- **Estructura formulaica** — intro-cuerpo-conclusion en cada seccion, siempre 3-5 puntos, transiciones predecibles

La humanizacion efectiva ataca estos tres ejes. Lo que NO funciona: sinonimos, typos, parafraseo, pedir "escribe como humano", subir temperature.

---

## Modos de operacion

### Modo REVIEW (default)

Analiza el texto y reporta:
- Patrones de IA detectados con ubicacion
- Severidad por patron
- Sugerencias de reescritura para cada hallazgo
- Score global de "naturalidad"

**No modifica el texto.** El usuario decide que cambiar.

### Modo REWRITE

Reescribe el texto aplicando todas las transformaciones.
Preserva el contenido y la intencion; cambia la voz y estructura.

El modo se determina por `$ARGUMENTS[0]`:
- `review` o sin argumento = modo review
- `rewrite` = modo rewrite

---

## FASE 1: Cargar texto

### 1.1 Resolver fuente

- Si `$ARGUMENTS` contiene un archivo, leerlo
- Si hay texto entre comillas, usarlo directamente
- Si no hay argumento de texto, preguntar al usuario

### 1.2 Detectar contexto

Identificar automaticamente (o preguntar):

| Contexto | Pistas |
|---|---|
| Documentacion tecnica | Archivo .md en repo, codigo, APIs |
| Informe/reporte | Estructura de secciones, datos, metricas |
| Ensayo/articulo | Argumentacion, tesis, referencias |
| Email/mensaje | Corto, dirigido a alguien, accion esperada |
| Blog post | Titulo, tono informal, publicacion |
| Academico | Citas, abstract, metodologia |

### 1.3 Identificar audiencia y registro

| Registro | Caracteristicas target |
|---|---|
| Tecnico entre pares | Jerga del dominio, directo, opiniones fuertes, contracciones |
| Profesional formal | Preciso pero no robotico, datos concretos, sin hedging vacio |
| Academico | Argumentacion rigurosa, engagement con fuentes, voz propia |
| Casual/blog | Primera persona, humor permitido, fragmentos, preguntas retoricas |

---

## FASE 2: Diagnostico — detectar patrones de IA

### 2.1 Vocabulario — palabras bandera

Buscar estas palabras/frases que son marcadores estadisticos de IA. No es que sean "malas palabras" — es que la IA las elige con frecuencia desproporcionada:

**Tier 1 — Señales fuertes (reemplazar siempre):**

```
delve, tapestry, landscape (metaforico), multifaceted, nuanced (como adjetivo decorativo),
pivotal, paramount, cornerstone, foster, leverage (como verbo), streamline, underscore,
intricate, realm, embark, navigate (metaforico), spearhead, groundbreaking, transformative,
game-changing, cutting-edge, holistic, synergy, robust (fuera de contexto tecnico),
seamless, comprehensive (como relleno), utilize, facilitate
```

**Tier 2 — Señales moderadas (evaluar en contexto):**

```
crucial, essential, vital, key (como adjetivo), significant, enhance, optimize,
implement, framework (fuera de codigo), ecosystem (fuera de biologia),
innovative, strategic, empower, drive (como "impulsar"), enable, ensure
```

**Tier 3 — Frases formulaicas (eliminar o reestructurar):**

```
"It's important to note that..."
"It's worth mentioning that..."
"In today's rapidly evolving..."
"In an era of..."
"This is a testament to..."
"At the end of the day..."
"Moving forward..."
"Let's dive in..."
"Without further ado..."
"In conclusion..."
"Overall, ..."
"In summary, ..."
"Firstly, ... Secondly, ... Thirdly, ..."
"On one hand... on the other hand..."
"This comprehensive guide..."
"This powerful tool..."
"Whether you're a... or a..."
```

### 2.2 Estructura — patrones formulaicos

| Patron | Señal de IA | Que buscar |
|---|---|---|
| Parrafos uniformes | Todos entre 60-120 palabras | Medir longitud de cada parrafo |
| Listas simetricas | Siempre 3 o 5 items, estructura paralela perfecta | Contar items, verificar paralelismo |
| Intro restatement | Primer parrafo repite el tema/pregunta | Leer apertura |
| Transiciones predecibles | "Furthermore", "Moreover", "Additionally" en cada parrafo | Contar transiciones formulaicas |
| Conclusion wrap-up | Ultimo parrafo empieza con "In conclusion", "Overall" | Leer cierre |
| Headers taxonomicos | Headers que suenan a indice de libro de texto | Evaluar headers |
| Sandwich structure | Cada seccion: intro + puntos + conclusion parcial | Evaluar estructura de secciones |

### 2.3 Ritmo — uniformidad de oraciones

Medir longitud de cada oracion (en palabras):

```
Perfil tipico de IA:   [15, 18, 14, 16, 19, 15, 17]  → varianza baja, todo ~16 palabras
Perfil tipico humano:  [4, 28, 12, 3, 35, 8, 22, 6]  → varianza alta, rafagas
```

**Metrica:** Si el rango (max - min) de longitud de oraciones en un parrafo es <15 palabras, es señal de IA.

### 2.4 Tono — neutralidad artificial

| Patron | Señal de IA |
|---|---|
| Hedging excesivo | Todo calificado con "might", "could", "potentially", "arguably" |
| Balance forzado | Siempre presenta "ambos lados" sin tomar posicion |
| Entusiasmo generico | "This amazing feature", "incredibly powerful" sin evidencia |
| Ausencia de persona | Sin "yo", "nosotros", sin anecdota, sin opinion directa |
| Diplomacia extrema | Nunca dice "esto esta mal" o "esto no sirve" |

---

## FASE 3: Transformacion (modo rewrite) / Sugerencias (modo review)

### Regla 1 — Ritmo roto (MAYOR IMPACTO)

La intervencion con mas retorno. Reescribir variando longitud de oraciones dramaticamente:

```
ANTES (IA):
"The implementation of this feature requires careful consideration of several
factors. These factors include performance implications, user experience
considerations, and maintainability concerns. Each of these aspects plays
a crucial role in determining the overall success of the project."

DESPUES (humano):
"Hay tres cosas que importan aqui: performance, UX, y mantenibilidad.
Las tres tiran para lados distintos. Si optimizas una, generalmente
sacrificas otra — y la tentacion de intentar las tres a la vez es
exactamente lo que mata proyectos. Elige dos."
```

**Reglas concretas:**
- Al menos una oracion de ≤6 palabras por parrafo
- Al menos una oracion de ≥25 palabras por parrafo
- Permitir fragmentos: "Exactamente eso." / "Ninguno."
- Permitir oraciones que empiezan con "Y", "Pero", "Porque"

### Regla 2 — Especificidad concreta

Reemplazar generalidades con detalles concretos:

```
ANTES: "This significantly improved performance."
DESPUES: "El query bajo de 3.2s a 180ms."

ANTES: "Many organizations face this challenge."
DESPUES: "Nos paso en el sprint de enero — perdimos dos semanas."

ANTES: "The results were impressive."
DESPUES: "42% mas de conversion. No me lo esperaba."
```

Si no hay datos concretos disponibles, preguntar al usuario o marcar con [DATO CONCRETO AQUI].

### Regla 3 — Eliminar hedging vacio

```
ANTES: "It's important to note that this approach might potentially help..."
DESPUES: "Este approach ayuda cuando..."

ANTES: "It could be argued that the implementation is somewhat complex."
DESPUES: "La implementacion es compleja."

ANTES: "There are several factors that should be taken into consideration."
DESPUES: "Tres cosas a considerar:"
```

**Test:** Si eliminar el hedge no cambia el significado, eliminarlo.

### Regla 4 — Voz y posicion

```
ANTES: "There are both advantages and disadvantages to this approach."
DESPUES: "Este approach resuelve X bien pero rompe Y. Para nuestro caso, vale la pena."

ANTES: "One could consider using microservices for this purpose."
DESPUES: "Usa microservicios. Un monolito no aguanta este nivel de concurrencia."
```

**Reglas:**
- Tomar una posicion. Si hay matiz, expresarlo como "X, pero ojo con Y"
- Usar primera persona cuando el contexto lo permite
- Incluir el razonamiento, no solo la conclusion

### Regla 5 — Estructura imperfecta

```
ANTES:
## Introduction
[parrafo uniforme]
## Key Considerations
[3 puntos perfectamente balanceados]
## Conclusion
[resumen de todo]

DESPUES:
## [Header directo, no generico]
[parrafo corto que va al grano]
[parrafo largo con el desarrollo]
[oracion suelta que cierra la idea — sin seccion de "conclusion"]
```

**Reglas:**
- No todos los parrafos necesitan topic sentence
- Variar longitud de parrafos (1 oracion, 5 oraciones, 3 oraciones)
- Eliminar secciones de "Introduction" y "Conclusion" explicitas
- Headers que digan algo especifico, no generico
- Permitir que una seccion termine sin cerrar — la siguiente puede retomar

### Regla 6 — Interrupciones y aside

```
ANTES: "The caching layer provides significant performance improvements
by storing frequently accessed data in memory."

DESPUES: "El cache mejora performance — y mucho, hablamos de 10x en
lecturas calientes — pero ojo: un cache mal invalidado es peor que no
tener cache."
```

- Parenteticos: (esto es clave)
- Dashes: — como interrupcion
- Auto-correccion: "Bueno, en realidad no es tan simple."
- Digresion breve que agrega contexto

### Regla 7 — Vocabulario de dominio

Reemplazar palabras genericas por el vocabulario real del campo:

```
ANTES: "Leverage the framework's robust capabilities to streamline the workflow."
DESPUES: "Usa los hooks de React para simplificar el flujo."

ANTES: "Implement a comprehensive solution for data persistence."
DESPUES: "Guarda en Room con cache invalidation por content hash."
```

Si el documento tiene dominio identificable, usar su jerga natural.

---

## FASE 4: Ajustes por tipo de documento

### Documentacion tecnica

- Registro: directo, imperativo, sin adornos
- Permitido: contracciones, fragmentos, opiniones sobre tradeoffs
- Prohibido: entusiasmo generico ("this powerful feature"), hedging
- Especial: incluir "por que" ademas de "como", usar nombres reales de funciones/APIs

### Informe/reporte

- Registro: profesional pero con voz
- Permitido: primera persona del plural, recomendaciones directas, datos concretos
- Prohibido: balance forzado, "on one hand/other hand", generalidades
- Especial: abrir con el hallazgo principal, no con contexto. Contexto despues

### Ensayo/articulo

- Registro: argumentativo con personalidad
- Permitido: primera persona, posiciones fuertes, preguntas retoricas
- Prohibido: "in today's world", listas de pros y cons sin posicion
- Especial: engagement real con fuentes (no solo "Segun X..."), contraargumentos que se responden

### Blog post

- Registro: conversacional, personalidad marcada
- Permitido: humor, anecdotas, fragmentos, una linea como parrafo, preguntas al lector
- Prohibido: TODA frase formulaica del Tier 3, estructura de textbook
- Especial: abrir con una historia o una afirmacion provocadora, no con definicion

### Email/mensaje

- Registro: directo, breve, accionable
- Permitido: contracciones, frases cortas, ir al grano en primera linea
- Prohibido: parrafos de >3 oraciones, hedging, formalidad innecesaria
- Especial: la accion esperada debe ser obvia sin tener que buscarla

---

## FASE 5: Reporte (modo review) / Verificacion (modo rewrite)

### Modo review — output

```markdown
## Diagnostico de naturalidad

### Score: N/10 (1 = claramente IA, 10 = indistinguible de humano)

### Hallazgos

**Vocabulario (N marcadores encontrados)**
- Linea 12: "delve" → reemplazar: "explorar", "meterse en", o eliminar
- Linea 34: "It's important to note that" → eliminar, ir directo al punto

**Estructura**
- Parrafos 2-5 tienen longitud casi identica (82, 78, 85, 80 palabras)
- 3 secciones siguen patron intro-3puntos-conclusion

**Ritmo**
- Rango de longitud de oraciones: 12-19 palabras (muy bajo, señal fuerte de IA)
- 0 oraciones de <6 palabras, 0 de >25 palabras

**Tono**
- 4 instancias de hedging sin contenido
- 0 opiniones directas o posiciones claras
- 0 uso de primera persona

### Recomendaciones prioritarias
1. [mayor impacto] Romper ritmo: agregar oraciones cortas y largas
2. Reemplazar N marcadores de vocabulario Tier 1
3. Eliminar hedging en lineas X, Y, Z
4. Tomar posicion en seccion N en vez de presentar "ambos lados"
```

### Modo rewrite — verificacion post

Despues de reescribir, verificar:
- [ ] Ningun marcador Tier 1 presente
- [ ] Rango de longitud de oraciones > 20 palabras por parrafo
- [ ] Al menos 1 parrafo de ≤2 oraciones y 1 de ≥4
- [ ] Hedging reducido >50% vs original
- [ ] Contenido factual preservado (nada inventado ni omitido)
- [ ] Registro consistente con el tipo de documento

Si alguna verificacion falla, ajustar antes de entregar.

## Argumento: $ARGUMENTS
