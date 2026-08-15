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
