import requests
from src.domain.ports.out_ports import ISemanticAnalyzerService

class JavaSemanticAdapter(ISemanticAnalyzerService):
    def evaluar_semantica(self, ast: dict) -> dict:
        try:
            # Mandamos el AST al microservicio de Java
            response = requests.post(
                "http://dsl_semantic_java:8080/api/evaluate", 
                json=ast,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                # Error semántico lanzado por Java 
                error_data = response.json()
                return {"error_semantico": error_data.get("mensaje", "Error semántico desconocido")}
            else:
                return {"error_semantico": "Error interno en el servidor semántico."}

        except requests.exceptions.RequestException as e:
            print(f"[SEMANTIC] Error de conexión con Java: {e}")
            return {"error_semantico": "No se pudo conectar con el microservicio semántico en Java."}
