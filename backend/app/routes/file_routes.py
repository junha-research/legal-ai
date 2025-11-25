# app/routes/file_routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.extractor import extract_text_from_file
from app.services.llm import analyze_contract
from app.models.legal import DocumentResult
from app.routes.legal import InterpretResponse
from app.nlp.extractor import build_nlp_info
from app.services.law_api import fetch_term_definitions




router = APIRouter(
    prefix="/api/files",
    tags=["files"],
)

@router.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    return {
        "filename": file.filename,
        "preview": text[:1000],
        "length": len(text),
    }


@router.post("/interpret", response_model=InterpretResponse)
async def interpret_file(
    file: UploadFile = File(...),
    language: str = Form("ko"),
):
    # ----------------------------------------------------
    # 1. 파일 → 텍스트 추출
    # ----------------------------------------------------
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="파일에서 텍스트를 추출하지 못했습니다.",
        )

    # ----------------------------------------------------
    # 2. NLP 분석
    # ----------------------------------------------------
    nlp_info = build_nlp_info(text, language_hint=language)

    # ----------------------------------------------------
    # 3. 법제처 용어 정의 조회
    # ----------------------------------------------------
    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # ----------------------------------------------------
    # 4. Gemini LLM 분석 호출
    # ----------------------------------------------------
    document: DocumentResult = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
    )

    # ----------------------------------------------------
    # 5. FastAPI ResponseModel에 맞춰 감싸서 반환 (필수)
    # ----------------------------------------------------
    return InterpretResponse(document=document)



