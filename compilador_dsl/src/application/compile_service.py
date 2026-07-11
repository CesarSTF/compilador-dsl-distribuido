import time
from src.infrastructure.config.settings import Settings
from src.domain.compiler.lexer import AutomataStrategy
from src.domain.compiler.parser import Parser
from src.domain.ports.out_ports import IErrorRecoveryService, ISemanticAnalyzerService

TOKENS_VALIDOS_LLM = {"UNIDAD_ORIGEN_C", "UNIDAD_DESTINO_F", "ERROR_LEXICO"}

class CompileService:
    def __init__(self, error_recovery_service: IErrorRecoveryService, semantic_service: ISemanticAnalyzerService):
        self.tokenizador = AutomataStrategy()
        self.parser = Parser()
        self.error_recovery = error_recovery_service
        self.semantic_service = semantic_service

    def compilar(self, entrada: str):
        if Settings.DEBUG: print(f"\n[*] Compilando: '{entrada}'")
        tiempo_inicio = time.time()
        
        # ═══════════════════════════════════════════
        # FASE 1: Análisis Léxico
        # ═══════════════════════════════════════════
        tokens_temporales = self.tokenizador.analizar(entrada)
        
        tokens_finales = [None] * len(tokens_temporales)
        errores_lexicos_buffer = []
        indices_errores = []

        for indice, token in enumerate(tokens_temporales):
            if token["tipo"] == "BUFFER_PLN":
                errores_lexicos_buffer.append({
                    "token": token["valor"].strip(),
                    "position": indice
                })
                indices_errores.append(indice)
            else:
                tokens_finales[indice] = token

        # Marcar los BUFFER_PLN como ERROR_LEXICO directamente
        for i, indice in enumerate(indices_errores):
            tokens_finales[indice] = {
                "tipo": "ERROR_LEXICO",
                "valor": errores_lexicos_buffer[i]["token"]
            }

        tiempo_fin = time.time()
        if Settings.DEBUG: print(f"[*] Fase Léxica en {tiempo_fin - tiempo_inicio:.2f}s")

        # ═══════════════════════════════════════════
        # FASE 2: Análisis Sintáctico
        # ═══════════════════════════════════════════
        arbol_sintactico = self.parser.parsear(tokens_finales)

        # ═══════════════════════════════════════════
        # FASE 3: Análisis Semántico (Java)
        # ═══════════════════════════════════════════
        resultado_semantico = None
        if "error_sintactico" not in arbol_sintactico:
            resultado_semantico = self.semantic_service.evaluar_semantica(arbol_sintactico)
            if "error_semantico" in resultado_semantico:
                arbol_sintactico["error_semantico"] = resultado_semantico["error_semantico"]
            else:
                arbol_sintactico["resultado_semantico"] = resultado_semantico

        # ═══════════════════════════════════════════
        # FASE 4: LLM (Análisis completo de errores)
        # ═══════════════════════════════════════════
        hay_errores_lexicos = any(t["tipo"] == "ERROR_LEXICO" for t in tokens_finales if t)
        hay_error_sintactico = "error_sintactico" in arbol_sintactico
        hay_error_semantico = "error_semantico" in arbol_sintactico

        if hay_errores_lexicos or hay_error_sintactico or hay_error_semantico:
            resultado_compilacion = {
                "codigo_fuente": entrada,
                "tokens": tokens_finales,
                "ast": arbol_sintactico
            }
            analisis_llm = self.error_recovery.analizar_errores(resultado_compilacion)
            arbol_sintactico["analisis_llm"] = analisis_llm

            # Retrocompatibilidad con frontend original: inyectar en tokens
            if "errores" in analisis_llm:
                for err in analisis_llm["errores"]:
                    if err.get("tipo_error") == "lexico" and err.get("token_problematico"):
                        # Buscar el token problemático y agregarle cause y suggestion
                        for t in tokens_finales:
                            if t and t["tipo"] == "ERROR_LEXICO" and t["valor"] == err["token_problematico"]:
                                t["cause"] = err.get("causa", "")
                                t["suggestion"] = err.get("sugerencia", "")

        return {
            "tokens": tokens_finales,
            "ast": arbol_sintactico
        }
