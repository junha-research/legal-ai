# backend/app/routes/legal.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.models.legal import DocumentResult
from app.nlp.extractor import build_nlp_info
from app.services.law_api import fetch_term_definitions
from app.services.llm import analyze_contract

router = APIRouter()


class InterpretRequest(BaseModel):
    text: str = Field(..., description="원본 계약/법률 텍스트 전체")
    language: Optional[str] = Field(None, description="ko/en/mixed 중 하나 (옵션)")

class InterpretResponse(BaseModel):
    document: Optional[DocumentResult] = None


@router.post("/interpret", response_model=InterpretResponse)
async def interpret_contract(req: InterpretRequest) -> InterpretResponse:
    """
    핵심 엔드포인트:
    - 조항 분리
    - 기본 태깅/NLP
    - 법제처 API 용어 정의
    - Gemini 기반 심층 리스크/인과관계 분석
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="분석할 텍스트가 비어 있습니다.")

    # 1) NLP 전처리 + 조항 추출 + 태그/파티 추론
    nlp_info = build_nlp_info(text, language_hint=req.language)

    # 2) 법제처 API로 용어 정의 조회 (명사 후보 리스트 기반)
    candidate_terms = nlp_info.candidate_terms
    term_map = {}
    if candidate_terms:
        term_map = await fetch_term_definitions(candidate_terms)

    # 3) LLM으로 전체 분석
    document = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
    )

    return InterpretResponse(document=document)
