# Alfabeto y Tabla de Tokens

## Alfabeto del Lenguaje (Σ)

El alfabeto aceptado por el compilador DSL se compone de los siguientes conjuntos de símbolos:

| Conjunto | Símbolos | Descripción |
|----------|---------|-------------|
| Letras minúsculas | `a-z` | Palabras reservadas y unidades |
| Letras mayúsculas | `A-Z` | Aceptadas por case-insensitive |
| Dígitos | `0-9` | Valores numéricos |
| Signo negativo | `-` | Para valores bajo cero |
| Punto decimal | `.` | Separador de decimales |
| Espacio en blanco | `\s` | Separador de lexemas |

## Palabras Reservadas

| Palabra | Token Generado |
|---------|---------------|
| `convertir` | `KW_CONVERTIR` |

## Tabla de Tokens

| Token | Lexemas Aceptados | Patrón Regex | Ejemplo |
|-------|------------------|-------------|---------|
| `KW_CONVERTIR` | convertir | `(?i:\bconvertir\b)` | "convertir" |
| `NUMERO` | Enteros, decimales y negativos | `-?\d+(\.\d+)?` | "100", "-500", "3.14" |
| `UNIDAD_ORIGEN_C` | grados centigrados, grados celsius, celsius | `(?i:\bgrados\s+centigrados\b\|\bgrados\s+celsius\b\|\bcelsius\b)` | "grados celsius" |
| `UNIDAD_DESTINO_F` | a fahrenheit, hacia fahrenheit | `(?i:\ba\s+fahrenheit\b\|\bhacia\s+fahrenheit\b)` | "a fahrenheit" |
| `ESPACIO` | Espacios en blanco | `\s+` | " " |
| `TEXTO_LN` | Cualquier texto residual | `[a-zA-Z]+` | "onzas", "xyz" |

## Tokens Especiales (Internos)

| Token | Origen | Descripción |
|-------|--------|-------------|
| `BUFFER_PLN` | AFD | Texto no reconocido agrupado, pendiente de análisis por el LLM |
| `ERROR_LEXICO` | LLM | Error irrecuperable devuelto por el modelo de IA |

## Prioridad de Evaluación

Los patrones se evalúan en el siguiente orden estricto (el primero que hace match gana):

1. `KW_CONVERTIR` — Palabra reservada
2. `NUMERO` — Valores numéricos
3. `UNIDAD_ORIGEN_C` — Unidad de origen (celsius)
4. `UNIDAD_DESTINO_F` — Unidad de destino (fahrenheit)
5. `ESPACIO` — Espacios (descartados)
6. `TEXTO_LN` — Residual (posible error léxico)
