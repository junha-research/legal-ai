# app/routes/file_routes.py
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.db.database import SessionLocal
from app.services.document_service import save_document_from_analysis

# 🔥 FIX: 올바른 extractor import
from app.services.extractor import extract_text_from_file

from app.services.llm import analyze_contract
from app.models.legal import DocumentResult
from app.routes.legal import InterpretResponse
from app.nlp.extractor import build_nlp_info
from app.services.law_api import fetch_term_definitions
from app.db.models import User

import google.generativeai as genai
from app.services.llm_prompt import build_contract_analysis_prompt
from app.deps.auth import get_current_user, get_db


router = APIRouter(
    prefix="/api/files",
    tags=["files"],
)


# ---------------------------------------------------------
# DB 종속성
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# STREAMING LLM 분석
# ---------------------------------------------------------
@router.post("/interpret-stream")
async def interpret_stream(
    file: UploadFile = File(...),
    language: str = Form("ko"),      # 🔥 프론트에서 보내는 언어
    db: Session = Depends(get_db),
):
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        return StreamingResponse(iter([f"error: {str(e)}"]), media_type="text/plain")

    nlp_info = build_nlp_info(text, language_hint=language)

    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # 🔥 언어 반영된 프롬프트 생성
    prompt = build_contract_analysis_prompt(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
        output_language=language,   # ★ 추가
    )

    model = genai.GenerativeModel("gemini-2.0-flash")

    async def event_generator():

        yield json.dumps({"stage": "start", "message": "LLM 분석 시작"}) + "\n"

        try:
            response = model.generate_content(
                prompt,
                stream=True,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4096,
                },
            )

            async for chunk in response:
                if hasattr(chunk, "text"):
                    yield json.dumps({
                        "stage": "chunk",
                        "content": chunk.text,
                    }) + "\n"

        except Exception as e:
            yield json.dumps({
                "stage": "error",
                "message": str(e),
            }) + "\n"
            return

        yield json.dumps({"stage": "done"}) + "\n"

    return StreamingResponse(event_generator(), media_type="text/plain")


# ---------------------------------------------------------
# 텍스트만 추출
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# 파일 기반 계약서 분석 + DB 저장
# ---------------------------------------------------------
@router.post("/interpret", response_model=InterpretResponse)
async def interpret_file(
    file: UploadFile = File(...),
    language: str = Form("ko"),            # 프론트에서 언어 전송
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    if not text.strip():
        raise HTTPException(400, "파일에서 텍스트가 없습니다.")

    nlp_info = build_nlp_info(text, language_hint=language)

    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # 🔥 언어 반영된 LLM 분석
    document: DocumentResult = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
        output_language=language,   # ★ 반드시 필요
    )

    summary_text = document.summary.overall_summary or "요약 없음"

    answer_markdown = (
        "```json\n"
        + json.dumps(document.dict(), indent=2, ensure_ascii=False)
        + "\n```"
    )

    saved = save_document_from_analysis(
        db=db,
        user_id=current_user.id,
        original_text=text,
        summary=summary_text,
        answer_markdown=answer_markdown,
    )

    document.document_id = str(saved.id)

    return InterpretResponse(document=document)


# ---------------------------------------------------------
# FULL PIPELINE: OCR + NLP + LLM + DB 저장
# ---------------------------------------------------------
@router.post("/full-interpret", response_model=InterpretResponse)
async def full_interpret(
    file: UploadFile = File(...),
    language: str = Form("ko"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    if not text.strip():
        raise HTTPException(400, "파일에서 텍스트를 추출하지 못했습니다.")

    nlp_info = build_nlp_info(text, language_hint=language)

    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # 🔥 언어 반영된 LLM 분석
    document: DocumentResult = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
        output_language=language,   # ★ 추가
    )

    summary_text = document.summary.overall_summary or "요약 없음"

    answer_markdown = (
        "```json\n"
        + json.dumps(document.dict(), indent=2, ensure_ascii=False)
        + "\n```"
    )

    saved = save_document_from_analysis(
        db=db,
        user_id=current_user.id,
        original_text=text,
        summary=summary_text,
        answer_markdown=answer_markdown,
    )

    document.document_id = str(saved.id)

    return InterpretResponse(document=document)
