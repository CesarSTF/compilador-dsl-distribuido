import re
from typing import List, Dict

class AutomataStrategy:
    def __init__(self):
        self.TOKEN_PATTERNS = [
            ("KW_CONVERTIR", r"(?i:\bconvertir\b)"),  
            ("NUMERO", r"-?\d+(\.\d+)?"),                
            ("UNIDAD_ORIGEN_C", r"(?i:\bgrados\s+centigrados\b|\bgrados\s+celsius\b|\bcelsius\b)"),
            ("UNIDAD_DESTINO_F", r"(?i:\ba\s+fahrenheit\b|\bhacia\s+fahrenheit\b)"),
            ("ESPACIO", r"\s+"),                      
            ("TEXTO_LN", r"[a-zA-Z]+")      
        ]
        self.regex = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in self.TOKEN_PATTERNS))

    def analizar(self, entrada: str) -> List[Dict]:
        tokens_finales = []
        buffer_texto = []

        for match in self.regex.finditer(entrada):
            tipo_token = match.lastgroup
            valor = match.group()

            if tipo_token == "ESPACIO":
                continue

            if tipo_token == "TEXTO_LN":
                buffer_texto.append(valor)
            else:
                if buffer_texto:
                    tokens_finales.append({"tipo": "BUFFER_PLN", "valor": " ".join(buffer_texto)})
                    buffer_texto.clear()
                tokens_finales.append({"tipo": tipo_token, "valor": valor})

        if buffer_texto:
            tokens_finales.append({"tipo": "BUFFER_PLN", "valor": " ".join(buffer_texto)})

        return tokens_finales
