from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Local Business Decision Maker Finder"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str = "sqlite:///./storage/app.db"
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: Path = Path("./storage/uploads")
    result_dir: Path = Path("./storage/results")
    export_dir: Path = Path("./storage/exports")
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, ge=1)
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    return settings

