# Seleccion de modelos para agentes Codex

Los pins deben corresponder a modelos que el host de Codex reconoce. La seleccion actual separa
calidad de analisis y costo de implementacion:

| Agente | Modelo | Esfuerzo | Motivo |
|---|---|---|---|
| prompt-artist | `gpt-6-astra` | medium | Sintesis creativa y seguimiento preciso de restricciones |
| reviewer | `gpt-6-astra` | high | Deteccion de regresiones y razonamiento entre archivos |
| security-auditor | `gpt-6-astra` | high | Analisis adversarial de alto riesgo |
| ui-reviewer | `gpt-6-astra` | high | Auditoria multimodal y de criterios cruzados |
| task-implementer | `gpt-5.6-sol` | medium | Trabajo agentico cotidiano con menor costo que los revisores |

La suite local valida configuracion, portabilidad y contratos; no reemplaza una comparacion de
calidad entre modelos. Antes de cambiar un pin se ejecutan los evals representativos del rol en el
host destino y se documentan modelo, fecha, casos, resultado y costo observado. Si no existe esa
evidencia, se conserva el pin actual.

El helper `scripts/bump-codex-model.sh` actualiza pins, pero no decide que modelo usar. Toda
actualizacion requiere revision del diff y la suite completa.
