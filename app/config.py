"""Application configuration via environment variables (.env supported)."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Skills git repo (mounted bind volume). Each subdir = one skill.
    skills_dir: str = "/data/skills"

    # Comma-separated API keys accepted as Bearer token or X-API-Key header.
    api_keys: str = "dev-key"

    # Shared secret for the Git webhook endpoint.
    webhook_secret: str = "change-me"

    # Runner (sandbox) configuration for script-type skills.
    runner_default_image: str = "python:3.12-slim"
    runner_memory: str = "128m"
    runner_cpus: float = 0.5
    runner_pids_limit: int = 64
    runner_timeout: int = 30  # seconds, hard kill
    runner_network: bool = False  # False => --network none
    runner_allow_sudo: bool = False

    # CORS (comma separated origins); default allow all for intranet.
    cors_origins: str = "*"

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def api_key_set(settings: Settings | None = None) -> set[str]:
    s = settings or get_settings()
    return {k.strip() for k in s.api_keys.split(",") if k.strip()}
