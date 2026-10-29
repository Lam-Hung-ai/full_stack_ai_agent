from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    # SQLAlchemy URL with the psycopg 3 driver (postgresql+psycopg://...).
    # dbmate cannot read this form; it uses DBMATE_DATABASE_URL instead.
    database_url: SecretStr
    db_pool_size: int = Field(default=10, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    # Fail fast when the pool is exhausted instead of hanging past proxy timeouts.
    db_pool_timeout: int = Field(default=10, ge=1)

    allowed_origins: list[str] = ["http://localhost:3000"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-sonnet-4.5"
    # "high" | "medium" | "low", or empty to turn reasoning off. Only takes effect
    # on models OpenRouter marks as reasoning-capable; streamed as AG-UI REASONING_*.
    openrouter_reasoning_effort: str | None = "high"
    # Optional, recommended by OpenRouter for attributing requests on their dashboard.
    openrouter_site_url: str | None = None
    openrouter_app_name: str | None = "agent-backend"

    @field_validator("database_url")
    @classmethod
    def _postgres_psycopg(cls, value: SecretStr) -> SecretStr:
        url = make_url(value.get_secret_value())
        if url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg://")
        return value

    @field_validator(
        "openrouter_reasoning_effort", "openrouter_site_url", "openrouter_app_name"
    )
    @classmethod
    def _blank_is_unset(cls, value: str | None) -> str | None:
        return value or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # pyrefly: ignore[missing-argument]
