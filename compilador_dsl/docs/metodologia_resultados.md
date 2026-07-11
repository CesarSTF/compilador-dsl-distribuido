# Resultados de la Metodología del Compilador DSL

Este documento expone los resultados tangibles y estructurales obtenidos tras la aplicación de cada fase metodológica en la construcción del Compilador DSL Distribuido.

## Fase 1: Definición Formal de la Gramática Libre de Contexto (GLC)
**Resultado:** Se definió un alfabeto y un conjunto estricto de símbolos terminales (tokens) que rigen el lenguaje del DSL.

| Token Oficial | Patrón Estructural Aceptado | Ejemplo |
|---|---|---|
| `KW_CONVERTIR` | Palabra reservada de acción | "convertir" |
| `NUMERO` | Enteros, decimales y negativos | "100", "-40", "3.14" |
| `UNIDAD_ORIGEN_C` | Variaciones de Celsius | "grados centigrados", "celsius" |
| `UNIDAD_DESTINO_F` | Variaciones hacia Fahrenheit | "a fahrenheit" |
| `ERROR_LEXICO` | Token especial asignado a entradas inválidas | "onzas" |

**Regla de Producción:** La gramática generada exige un orden inmutable y estricto para que la instrucción sea aceptada:
`[KW_CONVERTIR] + [NUMERO] + [UNIDAD_ORIGEN_C] + [UNIDAD_DESTINO_F]`

---

## Fase 2: Construcción del Escáner Léxico (AFD)
**Resultado:** Implementación de un Autómata Finito Determinista basado en patrones Regex (`lexer.py`) que consume el texto de izquierda a derecha.

| Estado | Patrón de Entrada (Regex) | Acción Automática |
|---|---|---|
| INICIO | `(?i:\bconvertir\b)` | Emitir `KW_CONVERTIR` |
| INICIO | `-?\d+(\.\d+)?` | Emitir `NUMERO` |
| INICIO | `(?i:\bgrados\s+centigrados\b\|\bgrados\s+celsius\b\|\bcelsius\b)` | Emitir `UNIDAD_ORIGEN_C` |
| INICIO | `(?i:\ba\s+fahrenheit\b\|\bhacia\s+fahrenheit\b)` | Emitir `UNIDAD_DESTINO_F` |
| INICIO | `[a-zA-Z]+` | Acumular en `BUFFER_PLN` (Texto residual) |
| INICIO | `\s+` | Descartar |

El mecanismo temporal `BUFFER_PLN` agrupa eficazmente entradas desconocidas aislando errores léxicos para no bloquear la lectura del resto de componentes.

---

## Fase 3: Integración del Módulo Semántico de Recuperación (LLM)
**Resultado:** Inyección estructurada de un modelo de IA local (`qwen2.5-coder:3b`) limitado y restringido por reglas duras. 

Se logró interceptar alucinaciones forzando al modelo a responder exclusivamente con un formato JSON estandarizado, mapeando las palabras desconocidas hacia sugerencias del propio sistema.
**Ejemplo de resolución del modelo ante una entrada errónea (`convertir 100 onzas a fahrenheit`):**
```json
{
  "tipo_error": "lexico",
  "token_problematico": "onzas",
  "causa": "El token 'onzas' no es reconocido por el autómata.",
  "sugerencia": "Elimine la palabra 'onzas' o reemplácela por 'grados centigrados' o 'celsius'."
}
```

---

## Fase 4: Orquestación Centralizada
**Resultado:** Construcción del núcleo `CompileService` como puente central de datos.

Se diseñó una **estrategia de validación unificada**. Para proteger los recursos del servidor y garantizar la estabilidad, el flujo orquesta la información secuencialmente, resolviendo el análisis en 4 saltos:
1. Lexer (Generación de Tokens) 
2. Parser (Validación de orden lógico)
3. Microservicio Java (Verificación de física térmica y matemáticas) 
4. LLM (Diagnóstico masivo post-compilación en caso de dispararse banderas de error en pasos anteriores).

---

## Fase 5: Análisis Sintáctico y Generación del Árbol (AST)
**Resultado:** Construcción jerárquica exitosa de la petición en formato AST-JSON, listo para ser consumido por la interfaz gráfica o cualquier API externa.

**Ejemplo de resultado de un AST validado sintácticamente y ejecutado por el microservicio Java (Regla de Celsius):**
```json
{
  "nodo_raiz": "COMANDO_CONVERSION",
  "hijos": [
    {"nodo": "ACCION", "valor": "convertir"},
    {"nodo": "VALOR", "valor": -20.0},
    {"nodo": "ORIGEN", "unidad": "UNIDAD_ORIGEN_C"},
    {"nodo": "DESTINO", "unidad": "UNIDAD_DESTINO_F"}
  ],
  "resultado_semantico": {
    "status": "success",
    "resultado_valor": -4.0,
    "resultado_texto": "-20.0 °C = -4.0 °F"
  }
}
```
