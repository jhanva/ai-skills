# Plataformas — Adaptación de prompts por modelo

## Gemini (Nano Banana Pro / Flash)

**Formato:** Prosa narrativa, sin sintaxis especial
**Negatives:** NO soporta negative prompts — usar framing positivo
**Texto:** Máximo 25 caracteres, comillas para texto literal
**Aspect ratios:** Especificar con imageSize en MAYÚSCULAS
**Referencia:** Soporta hasta 14 imágenes de referencia

```
Aspecto ratios soportados: 1:1, 3:4, 4:3, 9:16, 16:9, 2:3, 3:2,
1:2, 2:1, 9:21, 21:9, 4:5, 5:4, y auto
```

## Midjourney

**Formato:** Prosa narrativa + parámetros al final con `--`
**Parámetros clave:**

```
--ar 16:9        (aspect ratio)
--s 250          (stylize: 0-1000, default 100)
--c 20           (chaos: variación, 0-100)
--q 2            (quality: 0.25, 0.5, 1, 2)
--v 7            (versión del modelo)
--no trees       (negative prompts)
--style raw      (menos intervención estética de MJ)
```

**Conversión desde prosa:**
1. Mantener la prosa narrativa como prompt principal
2. Agregar parámetros al final
3. Midjourney responde bien a referencias artísticas y de equipamiento

**Ejemplo:**
```
A tired woman in her 30s at a rain-soaked bus stop, dampened wool coat,
paper coffee cup, peeling concert posters behind her, shot on Kodak
Portra 400 with 85mm lens, shallow depth of field --ar 2:3 --s 150 --v 7
```

## DALL-E (OpenAI)

**Formato:** Prosa narrativa pura, sin parámetros
**Fortalezas:** Sigue instrucciones de texto con precisión, buen text rendering
**Limitaciones:** Menos control estilístico que MJ, tiende a oversaturar
**Aspect ratios:** Solo 1:1, 16:9, 9:16 (limitar a estos)

**Optimizaciones:**
- DALL-E responde bien a descripciones de medios artísticos ("oil painting on canvas")
- Ser muy explícito con composición — DALL-E necesita más dirección que MJ
- Para texto en imagen: DALL-E es el mejor, especificar font style y placement
- Evitar "in the style of [artista vivo]" — OpenAI lo bloquea

## Stable Diffusion (SDXL / SD3)

**Formato:** Acepta tanto prosa como tags, pero prosa produce mejores resultados en SDXL+
**Negative prompt:** Soportado — se puede usar `Negative: [texto]` como sección separada
**CFG Scale:** Controla adherencia al prompt (7-12 recomendado)

**Conversión de tags a prosa:**

```
TAGS (viejo estilo):
masterpiece, best quality, 1girl, long hair, blue eyes, school uniform,
cherry blossoms, sunlight, depth of field, film grain

PROSA (mejor):
A young woman with flowing dark hair and striking blue eyes stands beneath
a canopy of cherry blossom trees, wearing a navy school uniform with a
white collar. Late afternoon sunlight filters through the petals, creating
dappled warm light across her face. Shot with shallow depth of field on
35mm film stock, natural grain texture.
```

**Parámetros típicos para incluir en metadata (no en prompt):**
```
Steps: 30-50
CFG: 7-12
Sampler: DPM++ 2M Karras o Euler a
Size: 1024x1024 (SDXL)
```

## Tabla rápida de conversión

| Concepto | Gemini | Midjourney | DALL-E | Stable Diffusion |
|---|---|---|---|---|
| Aspect ratio | Prosa + imageSize | `--ar 16:9` | Solo 3 opciones | Resolución en pixels |
| Negatives | Framing positivo | `--no X` | No soportado | Campo separado |
| Estilización | Prosa descriptiva | `--s N --style raw` | Prosa descriptiva | CFG + sampler |
| Calidad | Prosa descriptiva | `--q N` | Automático | Steps + CFG |
| Referencia | Imágenes adjuntas | URL en prompt | No soportado | img2img / IP-Adapter |
| Texto | Comillas + placement | Comillas (limitado) | Comillas (mejor) | ControlNet + inpaint |
