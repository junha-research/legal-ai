# backend/app/routes/contract_routes.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.deps.auth import get_current_user, get_db

from app.db.database import SessionLocal
from app.services.llm import analyze_contract
from app.services.document_service import save_document
from app.services.document_service import (
    list_documents,
    get_document,
)
from app.nlp.extractor import build_nlp_info
from app.services.law_api import fetch_term_definitions

from app.db.models import User, Document
from app.db.legal import Clause, Term



router = APIRouter(prefix="/contracts", tags=["Contract Analysis"])


# ---------------------------
# DB 의존성
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================
# 1) 계약서 전체 분석 + DB 저장 API
# =============================================
class ContractAnalyzeRequest(BaseModel):
    text: str
    filename: str = "uploaded.txt"
    language: str = "ko"   # 🔥 언어 선택 추가 (ko/en/vi)


class ContractAnalyzeResponse(BaseModel):
    document_id: int
    summary: str
    risk_score: int
    language: str


@router.post("/analyze", response_model=ContractAnalyzeResponse)
async def analyze_full_contract(
    req: ContractAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    TEXT 기반 계약서 분석 API
    """
    if not req.text.strip():
        raise HTTPException(400, "분석할 텍스트가 비었습니다.")

    # 1) NLP
    nlp_info = build_nlp_info(req.text, language_hint=req.language)

    # 2) 용어 정의
    term_definitions = await fetch_term_definitions(nlp_info.candidate_terms)

    # 3) LLM 분석 (🔥 UI 언어 반영)
    analysis: DocumentResult = await analyze_contract(
        original_text=req.text,
        nlp_info=nlp_info,
        term_definitions=term_definitions,
        output_language=req.language,  # 🔥 핵심
    )

    # 4) DB 저장
    saved = save_document(
        db=db,
        analysis=analysis,
        file_name=req.filename,
        user_id=current_user.id,
        language=req.language,   # 🔥 저장 시 언어 포함
    )

    # 5) 응답
    return ContractAnalyzeResponse(
        document_id=saved.id,
        summary=analysis.summary.overall_summary,
        risk_score=analysis.risk_profile.overall_risk_score,
        language=req.language,
    )


# =============================================
# 2) 문서 리스트 조회 API
# =============================================
@router.get("/list")
def list_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()

    return [
        {
            "id": d.id,
            "title": d.title,
            "summary": d.summary,
            "risk_score": d.risk_score,
            "created_at": d.created_at,
            "language": d.language,     # 🔥 언어 포함
            "is_favorite": d.is_favorite,
        }
        for d in docs
    ]


## =============================================
# 3) 문서 상세 조회 API (수정 버전)
# =============================================
@router.get("/{document_id}")
def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(404, "문서를 찾을 수 없습니다.")

    return {
        "id": doc.id,
        "title": doc.title,
        "summary": doc.summary,
        "risk_score": doc.risk_score,
        "risk_level": doc.risk_level or "중간",   # 🔥 추가
        "parties": doc.parties,
        "domain_tags": doc.domain_tags,
        "language": doc.language,
        "created_at": doc.created_at,
        "is_favorite": doc.is_favorite,
    }
# =============================================
# 4) 문서 조항 목록 조회 API
# =============================================
@router.get("/{document_id}/clauses")
def get_document_clauses(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 문서 검증
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(404, "문서를 찾을 수 없습니다.")

    clauses = db.query(Clause).filter(
        Clause.document_id == document_id
    ).order_by(Clause.id).all()

    return [
        {
            "id": c.id,
            "clause_id": c.clause_id,
            "title": c.title,
            "summary": c.summary,
            "risk_level": c.risk_level,
            "risk_score": c.risk_score,
        }
        for c in clauses
    ]


# =============================================
# 5) 문서 용어 목록 조회 API
# =============================================
@router.get("/{document_id}/terms")
def get_document_terms(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(404, "문서를 찾을 수 없습니다.")

    terms = db.query(Term).filter(
        Term.document_id == document_id
    ).order_by(Term.id).all()

    return [
        {
            "term": t.term,
            "korean": t.korean,
            "english": t.english,
            "source": t.source,
        }
        for t in terms
    ]


# =============================================
# 6) 문서 삭제 API
# =============================================
@router.delete("/{document_id}/delete")
def delete_contract(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(404, "문서를 찾을 수 없습니다.")

    # 자식 데이터 삭제
    db.query(Clause).filter(Clause.document_id == document_id).delete()
    db.query(Term).filter(Term.document_id == document_id).delete()

    db.delete(doc)
    db.commit()

    return {"message": "문서 삭제 완료", "document_id": document_id}


# =============================================
# 7) 문서 즐겨찾기 토글 API
# =============================================
@router.post("/{document_id}/favorite")
def toggle_favorite(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()

    if not doc:
        raise HTTPException(404, "문서를 찾을 수 없습니다.")

    doc.is_favorite = not doc.is_favorite
    db.commit()
    db.refresh(doc)

    return {
        "message": "즐겨찾기 상태 변경됨",
        "document_id": document_id,
        "is_favorite": doc.is_favorite,
    }
