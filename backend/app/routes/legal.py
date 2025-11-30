# backend/app/routes/legal.py

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import json
import secrets

# DB / 서비스 의존성
from app.db.database import SessionLocal
from app.services.document_service import save_document_from_analysis

# 모델 + NLP + LLM
from app.models.legal import DocumentResult
from app.nlp.extractor import build_nlp_info
from app.services.law_api import fetch_term_definitions
from app.services.llm import analyze_contract, generate_legal_answer_multilang

# DB 모델
from app.db.models import User, Conversation, Bookmark, ShareLink

from app.deps.auth import get_current_user, get_db

router = APIRouter()


# -----------------------------------------------------
# 📌 Request / Response 모델 정의
# -----------------------------------------------------

class InterpretRequest(BaseModel):
    text: str = Field(..., description="원본 계약/법률 텍스트 전체")
    language: Optional[str] = Field(None, description="ko/en/vie 중 하나")


class InterpretResponse(BaseModel):
    document: Optional[DocumentResult] = None


# -----------------------------------------------------
# 📌 DB 의존성
# -----------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------
# 📌 핵심 기능: 계약서 해석 + DB 저장
# -----------------------------------------------------
@router.post("/interpret", response_model=InterpretResponse)
async def interpret_contract(
    req: InterpretRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="분석할 텍스트가 비어 있습니다.")

    # 1) NLP 처리
    nlp_info = build_nlp_info(
        text,
        language_hint=req.language,
        force_language=req.language
    )
    # 2) 용어 정의 조회
    term_map = await fetch_term_definitions(nlp_info.candidate_terms)

    # 3) LLM 분석
    document: DocumentResult = await analyze_contract(
        original_text=text,
        nlp_info=nlp_info,
        term_definitions=term_map,
        output_language=req.language or "ko"

    )

    # 4) summary 생성
    summary_text = document.summary.overall_summary if document.summary else "요약 없음"

    # Markdown 저장용 JSON
    answer_markdown = "```json\n" + json.dumps(document.dict(), indent=2, ensure_ascii=False) + "\n```"

    # 5) DB 저장
    saved = save_document_from_analysis(
        db=db,
        user_id=current_user.id,
        original_text=text,
        summary=summary_text,
        answer_markdown=answer_markdown,
    )

    print("📌 Document Saved:", saved.id)

    return InterpretResponse(document=document)


# -----------------------------------------------------
# 📌 대화형 질의응답 (다국어)
# -----------------------------------------------------

class AskRequest(BaseModel):
    text: str
    language: Optional[str] = "ko"


@router.post("/ask")
async def ask_legal_question(
    req: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = Conversation(
        user_id=current_user.id,
        question=req.text,
        language=req.language or "ko",
        status="pending",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    try:
        answer = await generate_legal_answer_multilang(
            question=req.text,
            language=req.language or "ko"
        )
        conversation.answer = answer
        conversation.status = "completed"
        db.commit()
        db.refresh(conversation)

    except Exception as e:
        conversation.status = "error"
        conversation.answer = f"Error: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    return conversation


# -----------------------------------------------------
# 📌 히스토리 조회
# -----------------------------------------------------
@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).limit(100).all()


# -----------------------------------------------------
# 📌 북마크
# -----------------------------------------------------
@router.get("/bookmarks")
def get_bookmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Conversation).join(Bookmark).filter(
        Bookmark.user_id == current_user.id
    ).order_by(Bookmark.created_at.desc()).all()


@router.get("/is-bookmarked/{conversation_id}")
def is_bookmarked(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.conversation_id == conversation_id,
    ).first()
    return {"is_bookmarked": bookmark is not None}


class BookmarkToggle(BaseModel):
    conversation_id: int


@router.post("/toggle-bookmark")
def toggle_bookmark(
    req: BookmarkToggle,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.conversation_id == req.conversation_id,
    ).first()

    if bookmark:
        db.delete(bookmark)
        db.commit()
        return {"message": "북마크 제거", "is_bookmarked": False}
    else:
        db.add(Bookmark(
            user_id=current_user.id,
            conversation_id=req.conversation_id,
        ))
        db.commit()
        return {"message": "북마크 추가", "is_bookmarked": True}


# -----------------------------------------------------
# 📌 공유 링크
# -----------------------------------------------------
class ShareLinkCreate(BaseModel):
    conversation_id: int


@router.post("/create-share-link")
def create_share_link(req: ShareLinkCreate, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(
        Conversation.id == req.conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    existing = db.query(ShareLink).filter(
        ShareLink.conversation_id == req.conversation_id
    ).first()

    if existing:
        token = existing.token
    else:
        token = secrets.token_urlsafe(16)
        db.add(ShareLink(conversation_id=req.conversation_id, token=token))
        db.commit()

    return {"token": token, "url": f"http://localhost:5173/shared/{token}"}


@router.get("/shared/{token}")
def get_shared(token: str, db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()

    if not link:
        raise HTTPException(status_code=404, detail="공유 링크를 찾을 수 없습니다")

    return db.query(Conversation).filter(
        Conversation.id == link.conversation_id
    ).first()


# -----------------------------------------------------
# 📌 특정 대화 조회 + 삭제
# -----------------------------------------------------
@router.get("/conversation/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    return conv


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    db.delete(conv)
    db.commit()
    return {"message": "삭제 완료"}
