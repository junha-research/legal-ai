import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# backend/app/db/database.py의 절대 경로 기준
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/app/db
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))   # backend/

DB_PATH = os.path.join(ROOT_DIR, "legal_ai.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()