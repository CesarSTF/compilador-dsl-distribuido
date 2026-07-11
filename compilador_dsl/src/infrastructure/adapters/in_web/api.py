import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.infrastructure.config.settings import Settings
from src.infrastructure.adapters.out_db.mariadb_adapter import MariaDBHistoryRepository
from src.infrastructure.adapters.out_llm.ollama_adapter import OllamaErrorRecoveryAdapter
from src.infrastructure.adapters.out_semantic.java_semantic_adapter import JavaSemanticAdapter
from src.application.compile_service import CompileService

app = FastAPI(title="Compilador DSL API")

# Dependency Injection setup
db_repository = MariaDBHistoryRepository()
llm_recovery_service = OllamaErrorRecoveryAdapter()
semantic_analyzer = JavaSemanticAdapter()

compile_service = CompileService(
    error_recovery_service=llm_recovery_service,
    semantic_service=semantic_analyzer
)

@app.on_event("startup")
def startup_event():
    if Settings.NODE_ID == "nodo-1":
        db_repository.init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

class CodigoRequest(BaseModel):
    codigo: str

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/api/estado")
def estado_endpoint():
    return {
        "status": "online",
        "nodo_procesador": Settings.NODE_ID,
        "mensaje": f"El nodo {Settings.NODE_ID} está activo y procesando peticiones."
    }

@app.get("/api/historial")
def historial_endpoint():
    registros = db_repository.obtener_historial()
    return {
        "status": "success",
        "nodo_lector": Settings.NODE_ID,
        "fuente": "Slave DB (Replicación Asíncrona)",
        "registros": registros
    }

@app.post("/api/compilar")
def compilar_endpoint(request: CodigoRequest):
    tokens = compile_service.compilar(request.codigo)
    respuesta = {
        "status": "success",
        "nodo_procesador": Settings.NODE_ID,
        "codigo_original": request.codigo,
        "tokens_resultantes": tokens
    }
    
    db_repository.guardar_historial(
        codigo=request.codigo, 
        status="success" if "error_sintactico" not in tokens.get("ast", {}) else "error", 
        nodo=Settings.NODE_ID, 
        resultado=respuesta
    )
    
    print(flush=True)
    print(json.dumps(respuesta, indent=2, ensure_ascii=False), flush=True)
    return respuesta
