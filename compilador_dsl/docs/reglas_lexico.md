# Reglas del Análisis Léxico

## Autómata Finito Determinista (AFD)

El análisis léxico se implementa mediante un AFD basado en expresiones regulares compiladas. El autómata procesa la cadena de entrada de izquierda a derecha, consumiendo caracteres y generando tokens.

## Diagrama de Estados del AFD

```
              ┌─────────────┐
              │   INICIO    │
              └──────┬──────┘
                     │ Leer carácter
                     ▼
         ┌───────────────────────┐
         │  ¿Hace match con     │
         │  algún patrón regex? │
         └───────────┬──────────┘
                     │
            ┌────────┼────────┐
            ▼        ▼        ▼
       Token Válido  ESPACIO  TEXTO_LN
            │        │        │
            ▼        ▼        ▼
       Emitir     Descartar  Acumular
       Token                 en Buffer
            │                 │
            ▼                 ▼
       ¿Hay buffer?    ¿Siguiente es
       acumulado?      token válido?
            │                 │
         Sí ▼              Sí ▼
       Emitir            Emitir
       BUFFER_PLN        BUFFER_PLN
```

## Reglas de Transición

| Estado | Entrada | Acción | Estado Siguiente |
|--------|---------|--------|-----------------|
| INICIO | `convertir` | Emitir `KW_CONVERTIR` | INICIO |
| INICIO | `-` / `[0-9]+` | Emitir `NUMERO` | INICIO |
| INICIO | `grados centigrados` / `grados celsius` / `celsius` | Emitir `UNIDAD_ORIGEN_C` | INICIO |
| INICIO | `a fahrenheit` / `hacia fahrenheit` | Emitir `UNIDAD_DESTINO_F` | INICIO |
| INICIO | `\s+` | Descartar | INICIO |
| INICIO | `[a-zA-Z]+` | Acumular en buffer | BUFFER |
| BUFFER | Token válido encontrado | Emitir `BUFFER_PLN` + token válido | INICIO |
| BUFFER | Fin de cadena | Emitir `BUFFER_PLN` | FIN |

## Mecanismo de Buffer

El buffer de texto (`BUFFER_PLN`) es una estructura temporal que agrupa palabras no reconocidas consecutivas. Cuando el AFD vuelve a encontrar un token válido (como un número o una palabra reservada), "corta" el buffer y lo empaqueta como un error léxico pendiente.

### Ejemplo de Corte por Buffer

Entrada: `convertir 100 grados fahrenheit a 50 grados centigrados`

| Paso | Texto | Acción |
|------|-------|--------|
| 1 | `convertir` | → Emitir `KW_CONVERTIR` |
| 2 | `100` | → Emitir `NUMERO` |
| 3 | `grados` | → Acumular en buffer |
| 4 | `fahrenheit` | → Acumular en buffer |
| 5 | `a` | → Acumular en buffer |
| 6 | `50` | → CORTE: Emitir `BUFFER_PLN("grados fahrenheit a")` + `NUMERO(50)` |
| 7 | `grados centigrados` | → Emitir `UNIDAD_ORIGEN_C` |
