from abc import ABC, abstractmethod

class IErrorRecoveryService(ABC):
    @abstractmethod
    def analizar_errores(self, resultado_compilacion: dict) -> dict:
        pass

class ICompilationHistoryRepository(ABC):
    @abstractmethod
    def init_db(self) -> None:
        pass

    @abstractmethod
    def guardar_historial(self, codigo: str, status: str, nodo: str, resultado: dict) -> None:
        pass

    @abstractmethod
    def obtener_historial(self) -> list:
        pass

class ISemanticAnalyzerService(ABC):
    @abstractmethod
    def evaluar_semantica(self, ast: dict) -> dict:
        pass
