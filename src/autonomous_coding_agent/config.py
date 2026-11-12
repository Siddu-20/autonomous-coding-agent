"""Application configuration and environment settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # Application
    app_name: str = "Autonomous Coding Agent"
    environment: Literal["development", "testing", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # LLM configuration
    llm_provider: Literal["gemini", "anthropic"] = "gemini"
    llm_model: str | None = None

    gemini_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    # Optional persistence
    database_url: SecretStr | None = None

    # Workspace configuration
    workspace_root: Path = Path(".agent-workspaces")
    max_files_to_inspect: int = Field(default=1000, ge=1, le=10_000)
    max_file_size_bytes: int = Field(
        default=1_000_000,
        ge=1024,
        le=10_000_000,
    )

    # Agent execution
    max_retries: int = Field(default=3, ge=0, le=10)
    execution_timeout_seconds: int = Field(
        default=120,
        ge=1,
        le=3600,
    )
    max_output_bytes: int = Field(
        default=1_000_000,
        ge=1024,
        le=10_000_000,
    )

    # Docker sandbox configuration
    docker_image: str = "python:3.12-slim"
    docker_memory_limit_mb: int = Field(default=512, ge=128, le=8192)
    docker_cpu_limit: float = Field(default=1.0, gt=0, le=8)
    docker_pids_limit: int = Field(default=128, ge=1, le=1024)
    docker_network_disabled: bool = True

    @property
    def active_llm_api_key(self) -> SecretStr | None:
        """Return the API key corresponding to the selected LLM provider."""
        if self.llm_provider == "gemini":
            return self.gemini_api_key

        return self.anthropic_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()


__all__ = ["Settings", "get_settings"]
