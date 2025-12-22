from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    app_env: str = "dev"
    database_url: str = "sqlite:///./sentinelflow.db"
    log_level: str = "INFO"

    planner_mode: str = "heuristic"  # "llm" or "heuristic"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.2"



settings = Settings()
