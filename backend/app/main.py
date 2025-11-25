# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.legal import router as legal_router
from app.routes.file_routes import router as file_router


app = FastAPI(
    title="Legal AI Backend",
    description="계약서/법률 문서 심층 분석 API",
    version="1.0.0",
)

# CORS 설정 (프론트 연동 시 도메인 추가)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요 시 ["http://localhost:3000"] 등으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(legal_router, prefix="/api", tags=["legal"])
app.include_router(file_router)

