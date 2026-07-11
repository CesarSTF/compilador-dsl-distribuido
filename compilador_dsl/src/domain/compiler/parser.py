from typing import List, Dict

class Parser:
    def parsear(self, tokens: List[Dict]):
        for t in tokens:
            if t['tipo'] == "ERROR_LEXICO":
                msg = f"Error léxico irrecuperable en el token: '{t['valor']}'"
                if t.get('cause'):
                    msg += f". Causa: {t['cause']}"
                if t.get('suggestion'):
                    msg += f". Sugerencia: {t['suggestion']}"
                return {"error_sintactico": msg}
        if len(tokens) < 4:
            return {"error_sintactico": "Faltan argumentos. Estructura esperada: CONVERTIR [NUMERO] [ORIGEN] [DESTINO]"}

        ast = {
            "nodo_raiz": "COMANDO_CONVERSION",
            "hijos": []
        }
        
        if tokens[0]["tipo"] != "KW_CONVERTIR":
            return {"error_sintactico": f"Se esperaba 'convertir' al inicio, se encontró {tokens[0]['tipo']}"}
        ast["hijos"].append({"nodo": "ACCION", "valor": tokens[0]["valor"]})
            
        if tokens[1]["tipo"] != "NUMERO":
            return {"error_sintactico": f"Se esperaba un NUMERO, se encontró {tokens[1]['tipo']}"}
        ast["hijos"].append({"nodo": "VALOR", "valor": float(tokens[1]["valor"])})
            
        if tokens[2]["tipo"] not in ["UNIDAD_ORIGEN_C", "UNIDAD_DESTINO_F"]:
            return {"error_sintactico": f"Se esperaba unidad de origen, se encontró {tokens[2]['tipo']}"}
        ast["hijos"].append({"nodo": "ORIGEN", "unidad": tokens[2]["tipo"]})
            
        if tokens[3]["tipo"] not in ["UNIDAD_ORIGEN_C", "UNIDAD_DESTINO_F"]:
            return {"error_sintactico": f"Se esperaba unidad de destino, se encontró {tokens[3]['tipo']}"}
        ast["hijos"].append({"nodo": "DESTINO", "unidad": tokens[3]["tipo"]})
            
        return ast
