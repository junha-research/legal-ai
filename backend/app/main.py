# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.legal import router as legal_router
from app.routes.file_routes import router as file_router
from app.routes.law_routes import router as law_router
from app.routes.contract_routes import router as contract_router
from app.routes.legal import router as legal_router
from app.db.database import Base, engine
from app.routes.auth_test import router as auth_test

app = FastAPI(
    title="Legal AI Backend",
    description="계약서/법률 문서 심층 분석 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend-url.web.app",
        "https://your-render-app.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(legal_router, prefix="/api", tags=["legal"])
app.include_router(file_router)
app.include_router(law_router)
app.include_router(contract_router)
app.include_router(legal_router, prefix="/legal")
app.include_router(auth_test)



@app.on_event("startup")
def on_startup():
    print("📌 DB 초기화 중...")
    Base.metadata.create_all(bind=engine)
    print("📌 DB 테이블 생성 완료") 