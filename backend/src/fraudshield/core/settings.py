# FraudShield-Enterprise/backend/src/fraudshield/core/settings.py

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    model_config = {"protected_namespaces": ()}

    # Paths
    db_path: str = Field(
        default_factory=lambda: os.getenv("FRAUDSHIELD_DB_PATH", "fraudshield_core.db")
    )
    model_registry_path: str = Field(
        default_factory=lambda: os.getenv("MODEL_REGISTRY_PATH", "artifacts/models")
    )
    logs_path: str = Field(default_factory=lambda: os.getenv("LOGS_PATH", "logs"))
    reports_path: str = Field(default_factory=lambda: os.getenv("REPORTS_PATH", "reports"))

    # Security / compliance
    include_pii: bool = Field(
        default_factory=lambda: os.getenv("INCLUDE_PII", "false").strip().lower() == "true"
    )
    api_key: str = Field(default_factory=lambda: os.getenv("FRAUDSHIELD_API_KEY", ""))

    # CORS (comma-separated list)
    cors_allow_origins: str = Field(
        default_factory=lambda: os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:5173,http://localhost:8501",
        )
    )

    # LLM (only needed if ops extra installed)
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached settings object (singleton).
    Use get_settings() everywhere to avoid accidental re-parsing.
    """
    return Settings()

# Backward-compatible alias used across modules in this repository.
# Prefer get_settings() in new code.
def settings() -> Settings:
    return get_settings()
