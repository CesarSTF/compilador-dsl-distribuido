import pymysql
import json
import time
from src.infrastructure.config.settings import Settings
from src.domain.ports.out_ports import ICompilationHistoryRepository

class MariaDBHistoryRepository(ICompilationHistoryRepository):
    def _get_connection(self, host):
        """Obtiene una conexión a la base de datos especificada."""
        return pymysql.connect(
            host=host,
            user=Settings.DB_USER,
            password=Settings.DB_PASS,
            database=Settings.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )

    def init_db(self) -> None:
        """Crea la tabla en el nodo Maestro si no existe."""
        max_retries = 10
        for i in range(max_retries):
            try:
                connection = self._get_connection(Settings.DB_MASTER_HOST)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS historial_compilaciones (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            codigo_fuente TEXT NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            nodo_procesador VARCHAR(50) NOT NULL,
                            resultado_json TEXT NOT NULL,
                            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                connection.commit()
                connection.close()
                print("[DB] Tabla 'historial_compilaciones' inicializada en Master.")
                return
            except Exception as e:
                print(f"[DB] Esperando a que el Master levante... (Intento {i+1}/{max_retries}) - Error: {e}")
                time.sleep(5)

    def guardar_historial(self, codigo: str, status: str, nodo: str, resultado: dict) -> None:
        """Guarda un registro. ESCRITURA: Siempre al Nodo Master."""
        try:
            connection = self._get_connection(Settings.DB_MASTER_HOST)
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO historial_compilaciones 
                    (codigo_fuente, status, nodo_procesador, resultado_json) 
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (codigo, status, nodo, json.dumps(resultado, ensure_ascii=False)))
            connection.commit()
            connection.close()
        except Exception as e:
            print(f"[DB] Error guardando en Master: {e}")

    def obtener_historial(self) -> list:
        """Recupera los registros. LECTURA: Siempre al Nodo Esclavo."""
        try:
            connection = self._get_connection(Settings.DB_SLAVE_HOST)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, codigo_fuente, status, nodo_procesador, fecha 
                    FROM historial_compilaciones 
                    ORDER BY fecha DESC LIMIT 20
                """)
                result = cursor.fetchall()
            connection.close()
            return result
        except Exception as e:
            print(f"[DB] Error leyendo de Slave: {e}")
            return []
