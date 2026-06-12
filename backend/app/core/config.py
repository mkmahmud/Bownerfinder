from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Local Business Decision Maker Finder"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    job_execution_mode: str = "inline"
    database_url: str = "sqlite:///./storage/app.db"
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: Path = Path("./storage/uploads")
    result_dir: Path = Path("./storage/results")
    export_dir: Path = Path("./storage/exports")
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, ge=1)
    max_crawl_pages: int = Field(default=8, ge=1, le=32)
    search_timeout_seconds: float = Field(default=3.0, gt=0)
    crawl_timeout_seconds: float = Field(default=3.0, gt=0)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3"
    browser_headless: bool = True
    browser_rate_limit_seconds: float = Field(default=0.5, ge=0)
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings

