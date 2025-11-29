# backend/app/core/config.py

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# -----------------------------------------------------
# 📌 1) backend/.env 절대 경로 계산 (안전한 방식)
# -----------------------------------------------------
# 현재 파일 위치: backend/app/core/config.py
# parents[0] = core/
# parents[1] = app/
# parents[2] = backend/
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print(f"⚠️  .env 파일을 찾을 수 없습니다: {ENV_PATH}")


# -----------------------------------------------------
# 📌 2) Settings 정의
# -----------------------------------------------------
class Settings(BaseSettings):
    # --- API Keys ---
    GEMINI_API_KEY: Optional[str] = None
    MOLEG_API_KEY: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    SUPREME_COURT_API_KEY: Optional[str] = None

    # --- App Metadata ---
    DEBUG: bool = False
    APP_NAME: str = "Legal AI Backend"

    class Config:
        env_file = ENV_PATH
        env_file_encoding = "utf-8"
        extra = "ignore"


# -----------------------------------------------------
# 📌 3) settings 캐싱
# -----------------------------------------------------
@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
