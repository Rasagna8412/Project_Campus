"""Application Configuration Management."""

import json
from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "project_campus_dev.db").as_posix()


class Settings(BaseSettings):
    """Central configuration settings loaded from environment or .env file."""

    ENVIRONMENT: str = "development"
    APP_NAME: str = "Project Campus"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Configuration & Connection Pooling
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True
    LOG_LEVEL: str = "INFO"

    # Authentication & Session Security
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-campus-2026-xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_COOKIE_NAME: str = "campus_access_token"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"

    # Rate Limiting & Proxy Headers
    AUTH_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    # AI Tutor & Learning Engine Settings
    AI_PROVIDER: str = "deterministic"
    AI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL_NAME: str = "gemini-1.5-flash"
    AI_RATE_LIMIT_PER_MINUTE: int = 15
    SUBSCRIPTION_FREE_TIER_DAILY_TUTOR_LIMIT: int = 20
    SUBSCRIPTION_PRO_TIER_DAILY_TUTOR_LIMIT: int = 500

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Prevent silent deployment with insecure defaults in production."""
        if self.ENVIRONMENT.lower() == "production":
            if (
                not self.SECRET_KEY
                or "dev-insecure" in self.SECRET_KEY
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "Production environment requires a high-entropy SECRET_KEY (minimum 32 characters, no default dev keys)."
                )
            if not self.AUTH_COOKIE_SECURE:
                object.__setattr__(self, "AUTH_COOKIE_SECURE", True)
            if self.DEBUG:
                object.__setattr__(self, "DEBUG", False)
            if self.DB_POOL_SIZE < 1:
                raise ValueError("DB_POOL_SIZE must be at least 1 in production.")
            if self.DB_MAX_OVERFLOW < 0:
                raise ValueError("DB_MAX_OVERFLOW cannot be negative.")
            if not self.DATABASE_URL.startswith("sqlite"):
                if not (
                    self.DATABASE_URL.startswith("postgresql+asyncpg://")
                    or self.DATABASE_URL.startswith("postgresql+psycopg://")
                ):
                    raise ValueError(
                        "Production PostgreSQL database URL must specify an asynchronous driver (e.g. 'postgresql+asyncpg://...')."
                    )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
