# app/routes/file_routes.py
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.db.database import SessionLocal
from app.services.document_service import save_document_from_analysis
from app.services.extractor import extract_text_from_file
from app.services.llm import analyze_contract
from app.models.legal import DocumentResult
from app.routes.legal import InterpretResponse
from app.nlp.extractor import build_nlp_info
from app.services.law_api import fetch_term_definitions
from app.db.models import User
import google.generativeai as genai
import asyncio
from app.services.llm_prompt import build_contract_analysis_prompt
from app.deps.auth import get_current_user, get_db



"""
파일 업로드 기반 처리 라우터
- /extract-text → 텍스트 추출만
- /interpret → 파일 기반 계약서 분석 + DB 저장
- /full-interpret → OCR부터 LLM까지 풀 파이프라인 + DB 저장
"""

router = APIRouter(
    prefix="/api/files",
    tags=["files"],
)

# ---------------------------------------------------------
# DB 세션 종속성
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------
# STREAMING LLM 분석 라우터
# ------------------------------
@router.post("/interpret-stream")
async def interpret_stream(
    file: UploadFile = File(...),
    language: str = Form("ko"),
    db: Session = Depends(get_db),
):
    """
    파일 → 텍스트 추출 → NLP → 용어정의 → LLM 스트리밍
    """

    # 1) 텍스트 추출
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        return StreamingResponse(iter([f"error: {str(e)}"]), media_type="text/plain")

    # 2) NLP
    nlp_info = build_nlp_info(text, language_hint=language)

    # 3) 용어 정의 가져오기
    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # 4) LLM Prompt
    prompt = build_contract_analysis_prompt(text, nlp_info, term_map)

    model = genai.GenerativeModel("gemini-2.0-flash")

    # 5) 스트리밍 제너레이터
    async def event_generator():

        # 초기 단계 알림
        yield json.dumps({"stage": "start", "message": "LLM 분석 시작"}) + "\n"

        # Gemini 스트리밍
        try:
            response = model.generate_content(
                prompt,
                stream=True,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4096
                }
            )

            async for chunk in response:
                # 각 chunk는 text 형태
                if hasattr(chunk, "text"):
                    yield json.dumps({
                        "stage": "chunk",
                        "content": chunk.text
                    }) + "\n"

        except Exception as e:
            yield json.dumps({
                "stage": "error",
                "message": str(e)
            }) + "\n"
            return

        # 스트리밍 완료
        yield json.dumps({"stage": "done"}) + "\n"

    return StreamingResponse(event_generator(), media_type="text/plain")
# ---------------------------------------------------------
# Mock User (임시 인증) - legal.py와 동일
# ---------------------------------------------------------
from app.db.models import User

def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.open_id == "mock-user-123").first()
    if not user:
        user = User(
            open_id="mock-user-123",
            name="테스트 사용자",
            email="test@example.com",
            login_method="mock",
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# ---------------------------------------------------------
# 1) 파일에서 텍스트만 추출하는 엔드포인트 (저장 없음)
# ---------------------------------------------------------
@router.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    """
    PDF/DOCX/TXT/이미지에서 텍스트만 추출하는 API.
    프론트에서 '미리보기' 용도로 사용.
    """
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    return {
        "filename": file.filename,
        "preview": text[:1000],  # 너무 길면 잘라서 반환
        "length": len(text),
    }


# ---------------------------------------------------------
# 2) 파일 기반 계약서 해석 + DB 저장
# ---------------------------------------------------------
@router.post("/interpret", response_model=InterpretResponse)
async def interpret_file(
    file: UploadFile = File(...),
    language: str = Form("ko"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),


):
    """
    파일 업로드 → 텍스트 추출 → NLP → 용어정의 → LLM 분석
    + DB 자동 저장.

    legal.py(텍스트 기반)와 동일한 구조 유지.
    """

    # 1) 파일 → 텍스트 추출
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출하지 못했습니다.")

    # 2) NLP 분석
    nlp_info = build_nlp_info(text, language_hint=language)

    # 3) 용어 정의
    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # 4) LLM 분석
    document = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
    )

    # 5) DB 저장
    summary_text = document.summary.overall_summary if document.summary else "요약 없음"
    answer_markdown = "```json\n" + json.dumps(document.dict(), indent=2, ensure_ascii=False) + "\n```"

    saved = save_document_from_analysis(
        db=db,
        user_id=current_user.id,
        original_text=text,
        summary=summary_text,
        answer_markdown=answer_markdown,
    )


    print(f"Saved File Analyze Document ID: {saved.id}")

    return InterpretResponse(document=document)


# ---------------------------------------------------------
# 3) FULL PIPELINE 해석 + DB 저장
# ---------------------------------------------------------
@router.post("/full-interpret", response_model=InterpretResponse)
async def full_interpret(
    file: UploadFile = File(...),
    language: str = Form("ko"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

):
    """
    파일 기반 전체 파이프라인:
      - 파일 텍스트 추출(OCR 포함)
      - NLP 분석
      - 법제처 용어정의
      - Gemini 심층 분석
      - DB 저장
    """

    # 1) OCR/텍스트 추출
    try:
        text = await extract_text_from_file(file)
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출하지 못했습니다.")

    # 2) NLP
    nlp_info = build_nlp_info(text, language_hint=language)

    # 3) 용어 정의
    try:
        term_map = await fetch_term_definitions(nlp_info.candidate_terms)
    except Exception:
        term_map = {}

    # 4) LLM 분석
    document: DocumentResult = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
    )

    # 5) DB 저장
    summary_text = document.summary.overall_summary if document.summary else "요약 없음"
    answer_markdown = "```json\n" + json.dumps(document.dict(), indent=2, ensure_ascii=False) + "\n```"

    saved = save_document_from_analysis(
        db=db,
        user_id=current_user.id,
        original_text=text,
        summary=summary_text,
        answer_markdown=answer_markdown,
    )

    print(f"Saved FULL File Analyze Document ID: {saved.id}")

    return InterpretResponse(document=document)