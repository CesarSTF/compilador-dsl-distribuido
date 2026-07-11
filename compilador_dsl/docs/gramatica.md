# Gramática Libre de Contexto (GLC)

## Definición Formal

**G = (V, Σ, P, S)**

Donde:
- **V** (Variables / No terminales): `{COMANDO_CONVERSION, ACCION, VALOR, ORIGEN, DESTINO}`
- **Σ** (Terminales / Tokens): `{KW_CONVERTIR, NUMERO, UNIDAD_ORIGEN_C, UNIDAD_DESTINO_F}`
- **P** (Producciones): Las reglas de producción definidas abajo
- **S** (Símbolo inicial): `COMANDO_CONVERSION`

## Reglas de Producción

```
COMANDO_CONVERSION → ACCION VALOR ORIGEN DESTINO

ACCION             → KW_CONVERTIR

VALOR              → NUMERO

ORIGEN             → UNIDAD_ORIGEN_C
                   | UNIDAD_DESTINO_F

DESTINO            → UNIDAD_ORIGEN_C
                   | UNIDAD_DESTINO_F
```

## Estructura Aceptada

La única estructura válida que el parser acepta es:

```
[COMANDO] [VALOR_NUMÉRICO] [UNIDAD_DE_ORIGEN] [UNIDAD_DE_DESTINO]
```

### Ejemplos Válidos

| Entrada | Derivación |
|---------|-----------|
| `convertir 100 grados centigrados a fahrenheit` | KW_CONVERTIR → NUMERO → UNIDAD_ORIGEN_C → UNIDAD_DESTINO_F |
| `convertir 36.5 celsius a fahrenheit` | KW_CONVERTIR → NUMERO → UNIDAD_ORIGEN_C → UNIDAD_DESTINO_F |

### Ejemplos Inválidos

| Entrada | Error |
|---------|-------|
| `100 grados centigrados a fahrenheit` | Falta `KW_CONVERTIR` al inicio |
| `convertir grados centigrados a fahrenheit` | Falta `NUMERO` |
| `convertir 100 a fahrenheit` | Falta unidad de origen |
| `convertir 100 grados centigrados` | Falta unidad de destino |
| `convertir 100 onzas a fahrenheit` | `onzas` → `ERROR_LEXICO` |

## Árbol de Sintaxis Abstracta (AST)

Cuando la validación es exitosa, el parser construye el siguiente árbol:

```
         COMANDO_CONVERSION
        /    |       |      \
   ACCION  VALOR  ORIGEN  DESTINO
      |      |       |       |
 convertir  100  UNIDAD_C  UNIDAD_F
```

### Representación JSON del AST

```json
{
  "nodo_raiz": "COMANDO_CONVERSION",
  "hijos": [
    {"nodo": "ACCION", "valor": "convertir"},
    {"nodo": "VALOR", "valor": 100.0},
    {"nodo": "ORIGEN", "unidad": "UNIDAD_ORIGEN_C"},
    {"nodo": "DESTINO", "unidad": "UNIDAD_DESTINO_F"}
  ]
}
```
