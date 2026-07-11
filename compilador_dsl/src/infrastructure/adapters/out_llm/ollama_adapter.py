import json
import ollama
from src.infrastructure.config.settings import Settings
from src.domain.ports.out_ports import IErrorRecoveryService

class OllamaErrorRecoveryAdapter(IErrorRecoveryService):
    def __init__(self):
        self.modelo = Settings.LLM_MODEL

    def analizar_errores(self, resultado_compilacion: dict) -> dict:
        """
        Recibe el resultado COMPLETO de la compilación (tokens, AST, errores semánticos).
        Analiza los 3 tipos de errores: léxico, sintáctico y semántico.
        """
        prompt = f"""
Eres un experto en compiladores. Analiza el resultado de compilación de un DSL conversor de temperaturas.

═══════════════════════════════════════════
GRAMÁTICA DEL LENGUAJE
═══════════════════════════════════════════
Estructura válida: CONVERTIR [NUMERO] [UNIDAD_ORIGEN] [UNIDAD_DESTINO]

Tokens válidos:
- KW_CONVERTIR: "convertir"
- NUMERO: números enteros o decimales (ej. 100, 36.5)
- UNIDAD_ORIGEN_C: "grados centigrados", "celsius"
- UNIDAD_DESTINO_F: "a fahrenheit", "hacia fahrenheit"

Reglas semánticas:
- La temperatura no puede ser inferior al cero absoluto (-273.15 °C / -459.67 °F)
- No se puede convertir una unidad a sí misma

═══════════════════════════════════════════
RESULTADO DE COMPILACIÓN A ANALIZAR
═══════════════════════════════════════════
{json.dumps(resultado_compilacion, ensure_ascii=False, indent=2)}

═══════════════════════════════════════════
TIPOS DE ERROR Y CÓMO RESPONDER
═══════════════════════════════════════════

TIPO 1 - ERROR LÉXICO (token no reconocido por el autómata):
Ocurre cuando una palabra no coincide con ningún patrón del lexer.
Ejemplo de entrada: "convertir 100 celcius a fahrenheit"
El token "celcius" no coincide con "celsius" ni "grados centigrados".
Respuesta esperada:
{{
  "tipo_error": "lexico",
  "token_problematico": "celcius",
  "causa": "El token 'celcius' no es reconocido. Es un error tipográfico de 'celsius'.",
  "sugerencia": "Corrija 'celcius' por 'celsius' o 'grados centigrados'.",
  "correccion_posible": true
}}

TIPO 2 - ERROR SINTÁCTICO (estructura gramatical incorrecta o palabras mal combinadas):
Ocurre cuando los tokens están en orden incorrecto, faltan tokens obligatorios, o se combinan palabras válidas de forma incorrecta (ej. "hacia celsius").
Ejemplo de entrada 1: "100 grados centigrados a fahrenheit" (falta "convertir")
Respuesta esperada:
{{
  "tipo_error": "sintactico",
  "causa": "Falta la palabra clave 'convertir' al inicio del comando.",
  "sugerencia": "El comando debe iniciar con 'convertir'. Formato correcto: convertir [numero] [unidad_origen] [unidad_destino]",
  "ejemplo_corregido": "convertir 100 grados centigrados a fahrenheit"
}}

Ejemplo de entrada 2: "convertir 100 grados centigrados hacia celsius"
Respuesta esperada:
{{
  "tipo_error": "sintactico",
  "token_problematico": "hacia",
  "causa": "La expresión 'hacia celsius' es incorrecta. Solo se permite convertir 'a fahrenheit' o 'hacia fahrenheit'.",
  "sugerencia": "Cambie 'hacia celsius' por 'a fahrenheit'.",
  "ejemplo_corregido": "convertir 100 grados centigrados a fahrenheit"
}}

TIPO 3 - ERROR SEMÁNTICO (lógica o física incorrecta):
Ocurre cuando la gramática es correcta pero el significado no tiene sentido.
Ejemplo de entrada: "convertir -500 grados centigrados a fahrenheit" (bajo cero absoluto)
Respuesta esperada:
{{
  "tipo_error": "semantico",
  "causa": "La temperatura -500 °C es inferior al cero absoluto (-273.15 °C). No existe físicamente.",
  "sugerencia": "Use un valor de temperatura igual o superior a -273.15 °C.",
  "ejemplo_corregido": "convertir 100 grados centigrados a fahrenheit"
}}

Ejemplo semántico 2: "convertir 100 grados centigrados a centigrados" (misma unidad)
Respuesta esperada:
{{
  "tipo_error": "semantico",
  "causa": "No tiene sentido convertir Celsius a Celsius. Origen y destino son la misma unidad.",
  "sugerencia": "Cambie la unidad de destino a 'fahrenheit'.",
  "ejemplo_corregido": "convertir 100 grados centigrados a fahrenheit"
}}

═══════════════════════════════════════════
INSTRUCCIONES FINALES
═══════════════════════════════════════════
1. Analiza el resultado de compilación proporcionado arriba.
2. Identifica TODOS los errores presentes (pueden ser de múltiples tipos).
3. Responde ÚNICAMENTE con JSON válido siguiendo el formato de los ejemplos.
4. Si hay múltiples errores, devuelve una lista.
5. PROHIBIDO INVENTAR TOKENS O REGLAS SEMANTICAS EN LA RESPUESTA DE EJEMPLO, USA UNICAMENTE LAS QUE TE PASE AL INICIO DEL MENSAJE

Formato de respuesta:
{{
  "errores": [
    {{
      "tipo_error": "lexico|sintactico|semantico",
      "token_problematico": "texto del token (si aplica)",
      "causa": "explicación clara del error",
      "sugerencia": "cómo corregirlo",
      "ejemplo_corregido": "el comando corregido completo"
    }}
  ]
}}

No agregues texto adicional. No agregues markdown. Solo JSON.
"""
        try:
            respuesta = ollama.chat(model=self.modelo, messages=[
                {'role': 'user', 'content': prompt}
            ], format='json')
            contenido = respuesta['message']['content']
            
            if Settings.DEBUG:
                print("\n[LLM] Respuesta cruda del modelo:", flush=True)
                try:
                    print(json.dumps(json.loads(contenido), indent=2, ensure_ascii=False), flush=True)
                except Exception:
                    print(contenido, flush=True)
            
            return json.loads(contenido)
        except Exception as e:
            if Settings.DEBUG:
                print(f"\n[LLM] Error de conexión: {e}", flush=True)
            return {
                "errores": [
                    {
                        "tipo_error": "desconocido",
                        "causa": "No se pudo conectar con el modelo de IA.",
                        "sugerencia": "Verifique que Ollama esté ejecutándose correctamente."
                    }
                ]
            }
