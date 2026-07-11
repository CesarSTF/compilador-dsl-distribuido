# Compilador DSL — Conversor de Unidades de Temperatura

## Estructura del Proyecto

```
compilador_dsl/
├── .env                      # Variables de entorno (modelo LLM, workers, debug)
├── config.py                 # Cargador centralizado de configuraciones
├── requirements.txt          # Dependencias Python
├── main.py                   # Punto de entrada (Servidor FastAPI)
├── test_carga.py             # Script de prueba de concurrencia y balanceo
├── Dockerfile                # Receta de contenedor
├── docker-compose.yml        # Orquestación de nodos (192.168.1.10 y .11)
├── Makefile                  # Comandos de gestión rápida
├── lexico/
│   ├── __init__.py
│   ├── tokenizador.py        # Escáner AFD (AutomataStrategy)
│   └── spec.md               # Especificación del módulo
├── semantico/
│   ├── __init__.py
│   ├── llm_service.py        # Servicio LLM de recuperación de errores (LLMStrategy)
│   └── spec.md               # Especificación del módulo
├── sintactico/
│   ├── __init__.py
│   ├── parser.py             # Analizador sintáctico y constructor del AST (Parser)
│   └── spec.md               # Especificación del módulo
├── orquestador/
│   ├── __init__.py
│   ├── motor.py              # Motor central de coordinación (CompiladorOrquestador)
│   └── spec.md               # Especificación del módulo
└── docs/
    ├── estructura.md                # Este archivo
    ├── alfabeto_y_tokens.md         # Alfabeto y tabla de tokens
    ├── gramatica.md                 # Gramática Libre de Contexto (GLC)
    ├── reglas_lexico.md             # Reglas del análisis léxico
    ├── reglas_llm.md                # Reglas éticas y técnicas del LLM
    ├── flujo_compilacion.md         # Flujo completo de compilación
    └── arquitectura_distribuida.md  # Specs de distribución de carga y Nginx

## Tecnologías Utilizadas

| Componente | Tecnología |
|-----------|-----------|
| Lenguaje | Python 3.12 |
| Servidor Web | FastAPI + Uvicorn |
| Motor de IA | Ollama (qwen2.5-coder:3b) |
| Análisis Léxico | Expresiones Regulares (AFD) |
| Orquestación | Docker, Docker Compose, Nginx |

## Variables de Entorno (.env / Docker)

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `LLM_MODEL` | `qwen2.5-coder:3b` | Modelo de lenguaje local |
| `MAX_WORKERS` | `5` | Hilos concurrentes máximos |
| `DEBUG_MODE` | `True` | Habilita logs detallados en consola |
| `NODE_ID` | `nodo-1` | Identificador del nodo procesador (para Nginx) |

## API REST

### GET `/api/estado`
Utilizado para verificar la disponibilidad del nodo y comprobar el balanceo Round Robin de Nginx.

**Response:**
```json
{
  "status": "online",
  "nodo_procesador": "nodo-1",
  "mensaje": "El nodo nodo-1 está activo y procesando peticiones."
}
```

### POST `/api/compilar`

**Request Body (JSON):**
```json
{
  "codigo": "convertir 100 grados centigrados a fahrenheit"
}
```

**Response (Caso exitoso):**
```json
{
  "status": "success",
  "nodo_procesador": "nodo-2",
  "codigo_original": "convertir 100 grados centigrados a fahrenheit",
  "tokens_resultantes": {
    "tokens": [
      {"tipo": "KW_CONVERTIR", "valor": "convertir"},
      {"tipo": "NUMERO", "valor": "100"},
      {"tipo": "UNIDAD_ORIGEN_C", "valor": "grados centigrados"},
      {"tipo": "UNIDAD_DESTINO_F", "valor": "a fahrenheit"}
    ],
    "ast": {
      "nodo_raiz": "COMANDO_CONVERSION",
      "hijos": [
        {"nodo": "ACCION", "valor": "convertir"},
        {"nodo": "VALOR", "valor": 100.0},
        {"nodo": "ORIGEN", "unidad": "UNIDAD_ORIGEN_C"},
        {"nodo": "DESTINO", "unidad": "UNIDAD_DESTINO_F"}
      ]
    }
  }
}
```

**Response (Caso con error léxico):**
```json
{
  "status": "success",
  "nodo_procesador": "nodo-1",
  "codigo_original": "convertir 100 onzas a fahrenheit",
  "tokens_resultantes": {
    "tokens": [
      {"tipo": "KW_CONVERTIR", "valor": "convertir"},
      {"tipo": "NUMERO", "valor": "100"},
      {"tipo": "ERROR_LEXICO", "valor": "onzas", "cause": "...", "suggestion": "..."},
      {"tipo": "UNIDAD_DESTINO_F", "valor": "a fahrenheit"}
    ],
    "ast": {
      "error_sintactico": "Error léxico irrecuperable en el token: 'onzas'. Causa: ... Sugerencia: ..."
    }
  }
}
```
