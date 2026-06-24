from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Intern Match"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/intern_match"
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False

    storage_dir: Path = Path("storage/resumes")
    max_upload_mb: int = 10

    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1/chat/completions"
    llm_model: str = "gpt-4o-mini"

    frontend_dir: Path = Path("../frontend")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
