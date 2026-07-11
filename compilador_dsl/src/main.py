import uvicorn
from src.infrastructure.adapters.in_web.api import app

if __name__ == "__main__":
    print("Iniciando servidor en Arquitectura Hexagonal en http://localhost:8000")
    print("Frontend: http://localhost:8000")
    print("API POST: http://localhost:8000/api/compilar")
    uvicorn.run(app, host="0.0.0.0", port=8000)
