import os
import logging
from typing import List
from pydantic_settings import BaseSettings

logger = logging.getLogger("app.config")

DEFAULT_SECRET_KEY = "super-secret-key-change-in-production-min-32-chars"

class Settings(BaseSettings):
    PROJECT_NAME: str = "VR Mental Health Platform API"
    API_V1_STR: str = "/api/v1"

    # Environment Variables
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/vr_mental_health")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Vector store (Qdrant) + embedding pipeline
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "knowledge_chunks")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "auto")  # auto|gemini|fastembed
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    FASTEMBED_MODEL: str = os.getenv("FASTEMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5")
    FASTEMBED_SPARSE_MODEL: str = os.getenv("FASTEMBED_SPARSE_MODEL", "Qdrant/bm25")
    EMBEDDING_DIMENSION: int = os.getenv("EMBEDDING_DIMENSION", 768)
    CHUNK_SIZE_CHARS: int = os.getenv("CHUNK_SIZE_CHARS", 1000)
    CHUNK_OVERLAP_CHARS: int = os.getenv("CHUNK_OVERLAP_CHARS", 100)

    SECRET_KEY: str = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day (matches .env.example)

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    class Config:
        case_sensitive = True
        extra = "ignore"
        env_file = ".env"

    def model_post_init(self, __context) -> None:
        if self.SECRET_KEY in ("", DEFAULT_SECRET_KEY):
            logger.warning(
                "Using default SECRET_KEY. Set a strong random SECRET_KEY "
                "environment variable before any public or shared deployment."
            )

settings = Settings()
