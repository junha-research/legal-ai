# backend/app/core/config.py

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GEMINI_API_KEY: str
    MOLEG_API_KEY: Optional[str] = None
    DEBUG: bool = False

    APP_NAME: str = "Legal AI Backend"


@lru_cache
def get_settings() -> Settings:
    # 프로젝트 루트 기준으로 .env 로드
    root_dir = Path(__file__).resolve().parents[2]
    env_path = root_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    return Settings()


settings = get_settings()
