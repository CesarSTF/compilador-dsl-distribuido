# Reglas Éticas y Técnicas del LLM

## Propósito del LLM en el Compilador

El modelo de lenguaje (Ollama/qwen2.5-coder:3b) actúa **exclusivamente** como mecanismo de recuperación de errores léxicos. Su intervención está limitada a los siguientes casos:

- El AFD no pudo reconocer un fragmento de texto (generó un `BUFFER_PLN`).
- Se necesita determinar si el error es un typo recuperable o un token completamente inválido.

**El LLM NUNCA interviene si el AFD reconoce todos los tokens correctamente.**

## Restricciones Éticas

| # | Restricción |
|---|------------|
| 1 | No inventa nuevas unidades de medida |
| 2 | No sugiere unidades que no estén en la lista de tokens válidos |
| 3 | No inventa nuevos nombres de tokens |
| 4 | No combina palabras ni tokens |
| 5 | La causa debe ser técnica, breve y clara |
| 6 | La sugerencia debe estar orientada al usuario final |
| 7 | Solo puede mencionar unidades válidas del lenguaje (celsius, grados centigrados, fahrenheit) |

## Restricciones Técnicas

### Tokens Permitidos en la Respuesta
El campo `token_detectado` **SOLO** puede contener uno de estos tres valores:

| Valor | Uso |
|-------|-----|
| `UNIDAD_ORIGEN_C` | Cuando el texto es claramente un typo de celsius/grados centigrados |
| `UNIDAD_DESTINO_F` | Cuando el texto es claramente un typo de fahrenheit |
| `ERROR_LEXICO` | Cuando el texto no tiene relación con las unidades válidas |

### Validación Dura (Motor)
Independientemente de lo que el LLM devuelva, el orquestador aplica una validación:

```python
TOKENS_VALIDOS_LLM = {"UNIDAD_ORIGEN_C", "UNIDAD_DESTINO_F", "ERROR_LEXICO"}

if token_detectado not in TOKENS_VALIDOS_LLM:
    token_detectado = "ERROR_LEXICO"  # Forzado
```

Esto garantiza que aunque el LLM alucine e invente un token, el compilador **nunca** propagará un token inválido al parser.

## Formato de Respuesta Exigido

```json
{
  "errors": [
    {
      "lexema": "token inválido",
      "token_detectado": "ERROR_LEXICO",
      "cause": "explicación breve del error",
      "suggestion": "corrección sugerida"
    }
  ]
}
```

## Reglas de Decisión

| Caso | Ejemplo de Entrada | token_detectado | Justificación |
|------|-------------------|----------------|--------------|
| Typo de celsius | "celcius", "celsuis" | `UNIDAD_ORIGEN_C` | Error tipográfico evidente |
| Typo de fahrenheit | "farenheit", "farhenheit" | `UNIDAD_DESTINO_F` | Error tipográfico evidente |
| Unidad no soportada | "kelvin", "onzas", "litros" | `ERROR_LEXICO` | No existe en el lenguaje |
| Texto sin sentido | "abc", "perritos" | `ERROR_LEXICO` | Sin relación con temperatura |
| Fragmento mezclado | "grados fahrenheit a" | `ERROR_LEXICO` | Fragmento cortado por el AFD |

## Fallback de Seguridad

Si la conexión con Ollama falla o el modelo devuelve JSON inválido, el sistema genera automáticamente:

```json
{
  "errors": [
    {
      "lexema": "texto_original",
      "token_detectado": "ERROR_LEXICO",
      "cause": "La respuesta del modelo no fue un JSON válido.",
      "suggestion": "Elimine el token inválido."
    }
  ]
}
```
