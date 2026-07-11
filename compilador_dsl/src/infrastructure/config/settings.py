import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 5))
    DEBUG = os.getenv("DEBUG_MODE", "True").lower() in ("true", "1")
    NODE_ID = os.getenv("NODE_ID", "nodo-principal")
    DB_MASTER_HOST = os.getenv("DB_MASTER_HOST", "localhost")
    DB_SLAVE_HOST = os.getenv("DB_SLAVE_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "api_user")
    DB_PASS = os.getenv("DB_PASS", "api_password")
    DB_NAME = os.getenv("DB_NAME", "compilador_db")
