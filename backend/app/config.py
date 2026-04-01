"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the GATE Study Planner backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "GATE Study Planner"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/gate_planner"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/gate_planner"

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # ── Hugging Face ─────────────────────────────────────────
    hf_model_name: str = "google/flan-t5-large"
    hf_api_token: str = ""
    hf_use_api: bool = True
    hf_api_url: str = "https://api-inference.huggingface.co/models"

    # ── Sentence Transformers ────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── Celery ───────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    def get_cors_origins(self) -> List[str]:
        import json
        v = self.cors_origins.strip()
        if not v:
            return ["http://localhost:5173", "http://localhost:3000"]
        try:
            result = json.loads(v)
            return result if isinstance(result, list) else [result]
        except Exception:
            return [i.strip() for i in v.split(",") if i.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance (singleton per process)."""
    return Settings()
