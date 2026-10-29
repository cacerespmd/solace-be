
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_NAME = os.getenv("APP_NAME", "SOLACE")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))

    FRONTEND_URL = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    )

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv(
        "OPENAI_MODEL",
        "gpt-4.1-mini"
    )
    OPENAI_EMBEDDING_MODEL = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/solace.db"
    )
    
    # JWT Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    CHROMA_PERSIST_DIR = os.getenv(
        "CHROMA_PERSIST_DIR",
        "./data/chroma_db"
    )

    CHROMA_COLLECTION_NAME = os.getenv(
        "CHROMA_COLLECTION_NAME",
        "solace_knowledge_base"
    )

    CACHE_ENABLED = os.getenv(
        "CACHE_ENABLED",
        "true"
    ).lower() == "true"

    CACHE_TTL_SECONDS = int(
        os.getenv("CACHE_TTL_SECONDS", "3600")
    )

    AI_TEMPERATURE = float(
        os.getenv("AI_TEMPERATURE", "0.2")
    )

    AI_MAX_OUTPUT_TOKENS = int(
        os.getenv("AI_MAX_OUTPUT_TOKENS", "1000")
    )
    


settings = Settings()
