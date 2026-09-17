# Texto en imágenes y filtros de seguridad

## Texto en imágenes

### Reglas para texto exitoso

1. **Máximo 25 caracteres** por elemento de texto — modelos fallan con texto largo
2. **Máximo 2-3 elementos** de texto por imagen
3. **Comillas para texto literal:** `the word "SALE" in bold red letters`
4. **Describir tipografía, no nombrar fonts:**
   - Bien: "bold condensed sans-serif lettering"
   - Mal: "Helvetica Bold"
5. **Alto contraste obligatorio** entre texto y fondo
6. **Especificar ubicación:** "centered at the top third", "bottom-left corner"

### Técnica text-first

Cuando el texto es el elemento más importante de la imagen, ponerlo PRIMERO en el prompt:

```
The word "COFFEE" in warm brown hand-lettered script, centered on a
cream-colored background, surrounded by delicate watercolor illustrations
of coffee beans, steam wisps, and small leaves, vintage café menu aesthetic...
```

No al revés ("a coffee shop scene with the word COFFEE" — el texto se pierde).

### Elementos que mejoran text rendering

- Fondos simples y lisos detrás del texto
- Texto grande (ocupa al menos 20% del ancho de imagen)
- Colores sólidos para las letras (no gradientes)
- Serif o sans-serif simples (no scripts complejos)

---

## Filtros de seguridad

### Cómo funcionan

Los modelos tienen dos capas de filtro:
1. **Análisis del prompt** — rechaza antes de generar
2. **Análisis del output** — rechaza después de generar

### Categorías que disparan filtros

| Categoría | Trigger | Solución |
|---|---|---|
| Violencia explícita | Sangre, heridas, armas apuntando | Abstracción: "dramatic action scene", "warrior in battle stance" |
| Contenido sexual | Desnudez, poses sugestivas | Contexto artístico: "classical sculpture", "life drawing study" |
| Personas reales | Nombres de celebridades, políticos | Descripción de rasgos sin nombrar: "a woman with short silver hair" |
| Menores en riesgo | Niños en situaciones peligrosas | Reencuadrar con adultos o contexto seguro |
| Contenido médico | Heridas, procedimientos | "medical illustration style", "anatomical diagram" |
| Armas | Guns, explosivos | Contexto histórico/artístico: "antique dueling pistol in museum display" |

### Técnicas de reencuadre

**Abstracción artística:**
```
BLOQUEADO: "a soldier shooting a gun in a war zone"
VIABLE: "a lone figure silhouetted against billowing smoke, dramatic war
photography composition inspired by Robert Capa, high contrast black and white"
```

**Contexto museístico/académico:**
```
BLOQUEADO: "naked woman lying down"
VIABLE: "classical marble sculpture of a reclining figure, museum gallery
with soft directional spotlighting, smooth carved stone surface, Louvre collection"
```

**Metáfora visual:**
```
BLOQUEADO: "person dying"
VIABLE: "a withering flower in time-lapse, petals falling in slow motion,
dramatic single spotlight against darkness, memento mori still life"
```

### Reglas de reintento

- Máximo 3 intentos de reformulación
- Cada intento debe cambiar el approach, no solo las palabras
- Si 3 intentos fallan, la imagen probablemente no es genereable — informar al usuario
- NUNCA reintentar automáticamente sin ajustar el prompt
