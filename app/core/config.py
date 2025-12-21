from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./sentinelflow.db"
    log_level: str = "INFO"


settings = Settings()
