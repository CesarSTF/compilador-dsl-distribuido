# Flujo Completo de Compilación

## Diagrama de Fases

```
   Código Fuente (Usuario / Insomnia)
              │
              ▼
  ┌───────────────────────┐
  │   POST /api/compilar  │  ← FastAPI (main.py)
  └───────────┬───────────┘
              │
              ▼
  ┌───────────────────────┐
  │     ORQUESTADOR       │  ← motor.py
  │  (CompiladorOrquestador) │
  └───────────┬───────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌─────────┐     ┌─────────────┐
│  FASE 1 │     │   FASE 2    │
│ LÉXICA  │────►│  SEMÁNTICA  │  (Solo si hay errores)
│  (AFD)  │     │   (LLM)     │
└─────────┘     └──────┬──────┘
                       │
                       ▼
              ┌─────────────┐
              │   FASE 3    │
              │ SINTÁCTICA  │
              │  (Parser)   │
              └──────┬──────┘
                     │
                     ▼
              Respuesta JSON
```

## Fase 1: Análisis Léxico (Síncrono)

**Módulo:** `lexico/tokenizador.py` → `AutomataStrategy`
**Tiempo:** ~0ms (instantáneo)

El AFD escanea la cadena de entrada con expresiones regulares. Genera una lista de tokens temporales donde:
- Los tokens reconocidos se emiten directamente.
- El texto no reconocido se agrupa en `BUFFER_PLN`.

### Ejemplo

Entrada: `"convertir 100 perritos a fahrenheit"`

Salida del AFD:
```
[KW_CONVERTIR("convertir"), NUMERO("100"), BUFFER_PLN("perritos"), UNIDAD_DESTINO_F("a fahrenheit")]
```

## Fase 2: Recuperación de Errores (Condicional)

**Módulo:** `semantico/llm_service.py` → `LLMStrategy`
**Tiempo:** ~1-8s (depende del modelo)
**Condición:** Solo se ejecuta si existen tokens `BUFFER_PLN`.

1. El orquestador recopila todos los errores y sus posiciones originales.
2. Envía UNA SOLA solicitud al LLM con el código fuente + lista de errores.
3. El LLM analiza cada error y devuelve:
   - Token corregido (si es typo recuperable).
   - `ERROR_LEXICO` con causa y sugerencia (si es irrecuperable).
4. El orquestador aplica validación dura: si el LLM inventó un token, lo fuerza a `ERROR_LEXICO`.
5. Cada resultado se inserta en la posición original preservada.

### Si NO hay errores:
El LLM no se invoca (0.00s). La lista de tokens pasa directamente al parser.

## Fase 3: Análisis Sintáctico (Síncrono)

**Módulo:** `sintactico/parser.py` → `Parser`
**Tiempo:** ~0ms (instantáneo)

1. Primero busca tokens `ERROR_LEXICO`. Si existe alguno, aborta con error sintáctico (fail-fast).
2. Valida que la secuencia cumpla con la GLC: `KW_CONVERTIR → NUMERO → UNIDAD_ORIGEN → UNIDAD_DESTINO`.
3. Si la validación es exitosa, construye el Árbol de Sintaxis Abstracta (AST).

## Escenarios Completos

### Escenario 1: Código Correcto
```
Entrada: "convertir 100 grados centigrados a fahrenheit"

Fase 1 (AFD):  [KW_CONVERTIR, NUMERO, UNIDAD_ORIGEN_C, UNIDAD_DESTINO_F]
Fase 2 (LLM):  ❌ No interviene (0 errores)
Fase 3 (AST):  ✅ Árbol construido exitosamente
```

### Escenario 2: Error Tipográfico Recuperable
```
Entrada: "convertir 100 celcius a fahrenheit"

Fase 1 (AFD):  [KW_CONVERTIR, NUMERO, BUFFER_PLN("celcius"), UNIDAD_DESTINO_F]
Fase 2 (LLM):  "celcius" → UNIDAD_ORIGEN_C (typo corregido)
Fase 3 (AST):  ✅ Árbol construido exitosamente
```

### Escenario 3: Error Irrecuperable
```
Entrada: "convertir 100 onzas a fahrenheit"

Fase 1 (AFD):  [KW_CONVERTIR, NUMERO, BUFFER_PLN("onzas"), UNIDAD_DESTINO_F]
Fase 2 (LLM):  "onzas" → ERROR_LEXICO (unidad no soportada)
Fase 3 (AST):  ❌ Error sintáctico (token irrecuperable detectado)
```

### Escenario 4: Error de Sintaxis (Dos Números)
```
Entrada: "convertir 100 grados fahrenheit a 50 grados centigrados"

Fase 1 (AFD):  [KW_CONVERTIR, NUMERO(100), BUFFER_PLN("grados fahrenheit a"), NUMERO(50), UNIDAD_ORIGEN_C]
Fase 2 (LLM):  "grados fahrenheit a" → ERROR_LEXICO (fragmento mezclado)
Fase 3 (AST):  ❌ Error sintáctico (token irrecuperable detectado)
```
