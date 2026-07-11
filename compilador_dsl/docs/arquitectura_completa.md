# Compilador DSL Distribuido - Documentacion Completa del Sistema

## 1. Vision General

Sistema distribuido de compilacion para un DSL (Domain-Specific Language) de conversion de temperaturas. Implementa un pipeline completo: analisis lexico, sintactico, semantico (Java) y diagnostico inteligente (LLM). Desplegado sobre Docker con balanceo de carga via Nginx y base de datos replicada Master-Slave.

---

## 2. Diagrama de Despliegue

```
                    USUARIO (Navegador / Insomnia)
                             |
                        Puerto :80
                             |
                    +------------------+
                    |   Nginx (Host)   |
                    |   cesarServer    |
                    |   Round Robin    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     192.168.50.10:80              192.168.50.11:80
     +----------------+           +----------------+
     |  dsl_nodo1     |           |  dsl_nodo2     |
     |  Python/FastAPI|           |  Python/FastAPI|
     |  (Uvicorn)     |           |  (Uvicorn)     |
     +-------+--------+           +-------+--------+
              |                             |
              +------+-------+--------------+
                     |       |
         +-----------+  +----+--------+
         |              |             |
  +------+------+  +----+-----+ +----+----------+
  | dsl_semantic |  | db-master| | db-slave      |
  | _java        |  | MariaDB  | | MariaDB       |
  | SparkJava    |  | ESCRITURA| | LECTURA       |
  | :8080        |  | :3310    | | :3311         |
  +--------------+  +----------+ +---------------+
         |
  +------+------+
  | Ollama (Host)|
  | LLM Engine   |
  | :11434       |
  +--------------+
```

### 2.1 Tabla de Puertos

| Servicio | Contenedor | IP Interna (Docker) | Puerto Interno | Puerto Expuesto (Host) |
|---|---|---|---|---|
| Nginx (Balanceador) | Host nativo | 127.0.0.1 | 80 | 80 |
| Nodo Python 1 | dsl_nodo1 | 192.168.50.10 | 80 | - (solo via Nginx) |
| Nodo Python 2 | dsl_nodo2 | 192.168.50.11 | 80 | - (solo via Nginx) |
| Microservicio Java | dsl_semantic_java | DHCP Docker | 8080 | 8080 |
| MariaDB Master | dsl_db_master | DHCP Docker | 3306 | 3310 |
| MariaDB Slave | dsl_db_slave | DHCP Docker | 3306 | 3311 |
| Ollama (LLM) | Host nativo | 0.0.0.0 | 11434 | 11434 |

### 2.2 Red Docker

- **Nombre de red:** `compilador_dsl_app_network`
- **Subnet:** `192.168.50.0/24`
- **Driver:** bridge (default)
- Los nodos Python tienen IPs estaticas para que Nginx pueda apuntar a ellas.
- El resto de servicios reciben IP por DHCP de Docker dentro de la misma subnet.

---

## 3. Arquitectura Hexagonal (Puertos y Adaptadores)

El orquestador Python sigue una arquitectura hexagonal estricta:

```
src/
  main.py                          # Punto de entrada (uvicorn)
  application/
    compile_service.py             # CASO DE USO: orquesta todo el pipeline
  domain/
    compiler/
      lexer.py                     # Nucleo: Analisis Lexico (Automata)
      parser.py                    # Nucleo: Analisis Sintactico
    ports/
      out_ports.py                 # INTERFACES abstractas (ABC)
        - IErrorRecoveryService        -> analizar_errores(dict) -> dict
        - ISemanticAnalyzerService     -> evaluar_semantica(dict) -> dict
        - ICompilationHistoryRepository -> init_db, guardar, obtener
  infrastructure/
    config/
      settings.py                  # Configuracion desde ENV vars
    adapters/
      in_web/
        api.py                     # ADAPTADOR ENTRADA: FastAPI REST
      out_llm/
        ollama_adapter.py          # ADAPTADOR SALIDA: Ollama LLM
      out_semantic/
        java_semantic_adapter.py   # ADAPTADOR SALIDA: Java HTTP
      out_db/
        mariadb_adapter.py         # ADAPTADOR SALIDA: MariaDB
```

### 3.1 Interfaces (Puertos de Salida)

Definidas en `domain/ports/out_ports.py`:

```python
class IErrorRecoveryService(ABC):
    @abstractmethod
    def analizar_errores(self, resultado_compilacion: dict) -> dict: ...

class ISemanticAnalyzerService(ABC):
    @abstractmethod
    def evaluar_semantica(self, ast: dict) -> dict: ...

class ICompilationHistoryRepository(ABC):
    @abstractmethod
    def init_db(self) -> None: ...
    @abstractmethod
    def guardar_historial(self, codigo, status, nodo, resultado) -> None: ...
    @abstractmethod
    def obtener_historial(self) -> list: ...
```

### 3.2 Inyeccion de Dependencias

En `api.py`, los adaptadores se inyectan al servicio de aplicacion:

```python
llm_recovery_service = OllamaErrorRecoveryAdapter()
semantic_analyzer = JavaSemanticAdapter()
compile_service = CompileService(
    error_recovery_service=llm_recovery_service,
    semantic_service=semantic_analyzer
)
```

---

## 4. Pipeline de Compilacion (Flujo Completo)

El metodo `CompileService.compilar(entrada: str)` ejecuta 4 fases secuenciales:

### FASE 1: Analisis Lexico (`lexer.py`)

**Clase:** `AutomataStrategy`
**Patron:** Automata basado en expresiones regulares compiladas.

El lexer define 6 patrones de tokens:

| Token | Patron Regex | Ejemplo |
|---|---|---|
| `KW_CONVERTIR` | `(?i:\bconvertir\b)` | "convertir" |
| `NUMERO` | `\d+(\.\d+)?` | "100", "36.5" |
| `UNIDAD_ORIGEN_C` | `(?i:\bgrados\s+centigrados\b\|\bcelsius\b)` | "grados centigrados", "celsius" |
| `UNIDAD_DESTINO_F` | `(?i:\ba\s+fahrenheit\b\|\bhacia\s+fahrenheit\b)` | "a fahrenheit" |
| `ESPACIO` | `\s+` | (se ignora) |
| `TEXTO_LN` | `[a-zA-Z]+` | cualquier palabra no reconocida |

**Flujo interno del lexer:**

1. Se compila un unico regex gigante con grupos nombrados.
2. Se itera sobre todos los matches de la entrada.
3. Los tokens `ESPACIO` se descartan.
4. Los tokens `TEXTO_LN` se acumulan en un buffer temporal (`BUFFER_PLN`).
5. Cuando aparece un token valido despues de un buffer, el buffer se emite como token tipo `BUFFER_PLN` y luego el token valido.

**Post-procesamiento en CompileService:**

El `CompileService` toma los tokens del lexer y reclasifica los `BUFFER_PLN` como `ERROR_LEXICO`:

```python
for indice, token in enumerate(tokens_temporales):
    if token["tipo"] == "BUFFER_PLN":
        tokens_finales[indice] = {
            "tipo": "ERROR_LEXICO",
            "valor": errores_lexicos_buffer[i]["token"]
        }
```

**Ejemplo:**

Entrada: `"convertir 100 celcius a fahrenheit"`

Tokens resultantes:
```json
[
  {"tipo": "KW_CONVERTIR", "valor": "convertir"},
  {"tipo": "NUMERO", "valor": "100"},
  {"tipo": "ERROR_LEXICO", "valor": "celcius"},
  {"tipo": "UNIDAD_DESTINO_F", "valor": "a fahrenheit"}
]
```

### FASE 2: Analisis Sintactico (`parser.py`)

**Clase:** `Parser`
**Metodo:** `parsear(tokens) -> dict`

Valida la estructura gramatical. La gramatica esperada es:

```
COMANDO_CONVERSION ::= KW_CONVERTIR NUMERO UNIDAD_ORIGEN UNIDAD_DESTINO
```

**Reglas de validacion (en orden):**

1. Si algun token es `ERROR_LEXICO` -> retorna `error_sintactico` inmediatamente.
2. Si hay menos de 4 tokens -> error: "Faltan argumentos".
3. `tokens[0]` debe ser `KW_CONVERTIR`.
4. `tokens[1]` debe ser `NUMERO`.
5. `tokens[2]` debe ser `UNIDAD_ORIGEN_C` o `UNIDAD_DESTINO_F`.
6. `tokens[3]` debe ser `UNIDAD_ORIGEN_C` o `UNIDAD_DESTINO_F`.

**Salida exitosa (AST):**

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

**Salida con error:**

```json
{"error_sintactico": "Error lexico irrecuperable en el token: 'celcius'"}
```

### FASE 3: Analisis Semantico (Microservicio Java)

**Condicion de ejecucion:** Solo se ejecuta si NO hubo error sintactico en la Fase 2.

**Adaptador Python** (`java_semantic_adapter.py`):
- Envia el AST completo via HTTP POST a `http://dsl_semantic_java:8080/api/evaluate`
- Timeout: 5 segundos
- Si respuesta `200 OK`: resultado exitoso con conversion matematica
- Si respuesta `400 Bad Request`: error semantico (identidad, cero absoluto)
- Si excepcion de red: error generico

**Servidor Java** (`SemanticServer.java` - SparkJava en puerto 8080):

Recibe el AST en formato JSON. Extrae `valor`, `origen` y `destino` del array `hijos`.

**Reglas semanticas implementadas:**

| Regla | Condicion | HTTP Status | Mensaje |
|---|---|---|---|
| Identidad | `origen == destino` | 400 | "No tiene sentido convertir una unidad a si misma" |
| Cero Absoluto (C) | `origen == UNIDAD_ORIGEN_C && valor < -273.15` | 400 | "Temperatura inferior al cero absoluto (-273.15 C)" |
| Cero Absoluto (F) | `origen == UNIDAD_DESTINO_F && valor < -459.67` | 400 | "Temperatura inferior al cero absoluto (-459.67 F)" |

**Formulas de conversion:**

- Celsius a Fahrenheit: `resultado = (valor * 9.0 / 5.0) + 32`
- Fahrenheit a Celsius: `resultado = (valor - 32) * 5.0 / 9.0`
- Precision: 2 decimales (`Math.round(resultado * 100.0) / 100.0`)

**Respuesta exitosa de Java:**

```json
{
  "status": "success",
  "resultado_valor": 212.0,
  "resultado_texto": "100.0 C = 212.0 F",
  "mensaje_semantico": "Evaluado correctamente por Microservicio Java"
}
```

**Dependencias Java (pom.xml):**
- `spark-core:2.9.4` (servidor HTTP ligero)
- `gson:2.10.1` (serializacion JSON)
- `slf4j-simple:1.7.36` (logging requerido por Spark)
- Build: Maven Assembly Plugin genera fat-jar
- JDK: Eclipse Temurin 17

### FASE 4: Diagnostico Inteligente (LLM via Ollama)

**Condicion de ejecucion:** Solo se ejecuta si hay AL MENOS UN error (lexico, sintactico o semantico).

**Modelo:** `qwen2.5-coder:3b` (configurable via ENV `LLM_MODEL`)
**Conexion:** `http://host.docker.internal:11434` (Ollama corriendo en el host)

**Adaptador Python** (`ollama_adapter.py`):

1. Construye un prompt estructurado que incluye:
   - La gramatica completa del DSL
   - Las reglas semanticas (cero absoluto, identidad)
   - El resultado completo de compilacion (tokens + AST + errores previos)
   - Ejemplos concretos de respuesta para cada tipo de error
   - Instruccion de responder SOLO en JSON valido

2. Invoca `ollama.chat()` con `format='json'` para forzar JSON output.

3. Parsea la respuesta JSON del modelo.

**Formato de respuesta del LLM:**

```json
{
  "errores": [
    {
      "tipo_error": "lexico|sintactico|semantico",
      "token_problematico": "celcius",
      "causa": "El token 'celcius' no es reconocido...",
      "sugerencia": "Corrija 'celcius' por 'celsius'...",
      "correccion_posible": true,
      "ejemplo_corregido": "convertir 100 celsius a fahrenheit"
    }
  ]
}
```

**Retrocompatibilidad con frontend:**

Despues de obtener la respuesta del LLM, el `CompileService` inyecta los campos `cause` y `suggestion` directamente en los tokens `ERROR_LEXICO` del array de tokens finales, para que el frontend pueda renderizarlos debajo de cada token erroneo:

```python
if err.get("tipo_error") == "lexico" and err.get("token_problematico"):
    for t in tokens_finales:
        if t and t["tipo"] == "ERROR_LEXICO" and t["valor"] == err["token_problematico"]:
            t["cause"] = err.get("causa", "")
            t["suggestion"] = err.get("sugerencia", "")
```

---

## 5. Balanceo de Carga (Nginx)

### 5.1 Configuracion

Archivo: `/etc/nginx/conf.d/balanceador.conf` (en el host)

```nginx
upstream servers {
    server 192.168.50.10;
    server 192.168.50.11;
}

server {
    listen 80;
    server_name cesarServer;

    location / {
        proxy_pass http://servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5.2 Resolucion DNS

En `/etc/hosts` del host:
```
127.0.0.1 cesarServer
```

### 5.3 Algoritmo

Round Robin por defecto de Nginx. Cada peticion HTTP alterna entre nodo-1 y nodo-2.

---

## 6. Base de Datos Replicada

### 6.1 Topologia

- **Master** (`dsl_db_master`): Recibe todas las ESCRITURAS.
- **Slave** (`dsl_db_slave`): Recibe todas las LECTURAS. Se replica asincronamente del Master.

### 6.2 Configuracion de Replicacion

| Variable | Master | Slave |
|---|---|---|
| `MARIADB_REPLICATION_MODE` | master | slave |
| `MARIADB_REPLICATION_USER` | repl_user | repl_user |
| `MARIADB_REPLICATION_PASSWORD` | repl_password | repl_password |
| `MARIADB_MASTER_HOST` | - | db-master |

### 6.3 Esquema de Base de Datos

```sql
CREATE TABLE IF NOT EXISTS historial_compilaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_fuente TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    nodo_procesador VARCHAR(50) NOT NULL,
    resultado_json TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.4 Patron de Lectura/Escritura

- `guardar_historial()` -> conecta a `DB_MASTER_HOST` (escritura)
- `obtener_historial()` -> conecta a `DB_SLAVE_HOST` (lectura)
- La tabla se inicializa solo en nodo-1 (`startup_event` con condicion `NODE_ID == "nodo-1"`)

---

## 7. API REST (Endpoints)

### POST `/api/compilar`

**Request:**
```json
{"codigo": "convertir 100 grados centigrados a fahrenheit"}
```

**Response (exito):**
```json
{
  "status": "success",
  "nodo_procesador": "nodo-1",
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
      "hijos": [...],
      "resultado_semantico": {
        "status": "success",
        "resultado_valor": 212.0,
        "resultado_texto": "100.0 C = 212.0 F",
        "mensaje_semantico": "Evaluado correctamente por Microservicio Java"
      }
    }
  }
}
```

### GET `/api/estado`

Devuelve el estado del nodo que procesa la peticion.

### GET `/api/historial`

Lee las ultimas 20 compilaciones desde el Slave DB.

---

## 8. Frontend

### 8.1 Stack

- HTML5 semantico (`index.html`)
- CSS puro con variables custom y tema oscuro (`style.css`)
- JavaScript vanilla (`app.js`)
- Tipografias: Inter (UI), JetBrains Mono (codigo)

### 8.2 Funcionalidad

1. Editor de codigo con placeholder y contador de caracteres.
2. Chips de ejemplos rapidos (click para compilar automaticamente).
3. Panel de Tokens: muestra cada token con badge de color segun tipo.
4. Panel AST: muestra el arbol o los errores detectados.
5. Panel de Respuesta LLM: caja azul con diagnostico inteligente.
6. Panel JSON: respuesta cruda del servidor.
7. Panel Historial: lee compilaciones previas desde el Slave DB.

### 8.3 Renderizado de Errores

El frontend renderiza 3 niveles de informacion de error:

1. **Errores del compilador** (rojo): Error sintactico/lexico del parser.
2. **Errores semanticos** (rojo): Error del microservicio Java.
3. **Respuesta LLM** (azul): Diagnostico inteligente con causa, sugerencia y ejemplo corregido.

---

## 9. Contenedorizacion (Docker)

### 9.1 Dockerfile Python

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]
```

### 9.2 Dockerfile Java (Multi-stage)

```dockerfile
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /app/target/semantic-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar ./semantic.jar
EXPOSE 8080
CMD ["java", "-jar", "semantic.jar"]
```

### 9.3 Dependencias Python

```
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
ollama>=0.1.0
python-dotenv>=1.0.0
pymysql>=1.1.1
requests>=2.31.0
```

---

## 10. Comandos de Operacion (Makefile)

```makefile
make up        # docker compose up -d
make down      # docker compose down
make build     # docker compose up -d --build
make restart   # docker compose restart
make logs      # docker compose logs -f
make test      # python test_carga.py
```

---

## 11. Prueba de Carga

El script `test_carga.py` usa `aiohttp` para enviar 100 peticiones concurrentes al balanceador y verificar la distribucion Round Robin entre nodos.

---

## 12. Configuracion del Host

### 12.1 Ollama

Ollama debe escuchar en todas las interfaces para que los contenedores Docker puedan acceder:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo bash -c 'echo -e "[Service]\nEnvironment=\"OLLAMA_HOST=0.0.0.0\"" > /etc/systemd/system/ollama.service.d/override.conf'
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

### 12.2 DNS Local

```bash
sudo bash -c 'echo "127.0.0.1 cesarServer" >> /etc/hosts'
```

### 12.3 Nginx

```bash
sudo apt install nginx
# Crear /etc/nginx/conf.d/balanceador.conf con la config de la seccion 5
sudo systemctl restart nginx
```

---

## 13. Ejemplos de Prueba

### Compilacion Exitosa

Entrada: `convertir 100 grados centigrados a fahrenheit`
Resultado: 212.0 F - Sin errores, AST completo, resultado del microservicio Java.

### Error Lexico (typo)

Entrada: `convertir 100 celcius a fahrenheit`
Resultado: Token "celcius" marcado como ERROR_LEXICO. LLM sugiere corregir a "celsius".

### Error Sintactico (falta keyword)

Entrada: `100 grados centigrados a fahrenheit`
Resultado: Faltan argumentos. LLM sugiere agregar "convertir" al inicio.

### Error Semantico (misma unidad)

Entrada: `convertir 100 celsius celsius`
Resultado: Java retorna error 400: "No tiene sentido convertir una unidad a si misma."

### Error Semantico (cero absoluto)

Entrada: `convertir -500 grados centigrados a fahrenheit`
Resultado: Java retorna error 400: "Temperatura inferior al cero absoluto."
