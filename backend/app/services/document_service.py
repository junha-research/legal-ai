# backend/app/services/document_service.py

from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session

# DB 테이블
from app.db.models import Document
from app.db.legal import Clause, Term

# LLM 분석 결과 모델
from app.models.legal import DocumentResult


# ======================================================================================
# 1) 간단한 Q&A 저장 (기존 기능)
# ======================================================================================
def save_document_from_analysis(
    db: Session,
    user_id: int,
    original_text: str,
    summary: str,
    answer_markdown: str,
    language: str = "ko"   # 🔥 추가
):
    """
    🔵 Q&A 저장용 문서 기록
    """
    doc = Document(
        user_id=user_id,
        original_text=original_text,
        summary=summary,
        answer_markdown=answer_markdown,
        language=language,    # 🔥 추가 저장
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ======================================================================================
# 2) 전체 계약 분석 저장 (Document + Clause + Term)
# ======================================================================================
def save_document(
    db: Session,
    analysis: DocumentResult,
    file_name: str,
    user_id: Optional[int] = None,
    language: Optional[str] = None,   # 🔥 추가
):
    """
    🟣 계약서 분석 전체 저장 기능
    """

    # 언어 선택 규칙
    lang = (
        language
        or getattr(analysis.meta, "language", None)
        or "ko"
    )

    # ---------------------------
    # Document 저장
    # ---------------------------
    doc = Document(
        user_id=user_id,
        title=analysis.summary.title or file_name,
        original_text="",  # 필요하면 OCR 텍스트 저장 가능
        summary=analysis.summary.overall_summary,
        answer_markdown="",

        # ---- 메타 ---
        language=lang,
        parties=",".join(analysis.meta.parties or []),
        domain_tags=",".join(analysis.meta.domain_tags or []),

        # ---- 리스크 ---
        risk_level=analysis.risk_profile.overall_risk_level,
        risk_score=analysis.risk_profile.overall_risk_score,
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    # ---------------------------
    # Clause 저장
    # ---------------------------
    for c in analysis.clauses:
        clause = Clause(
            document_id=doc.id,
            clause_id=c.clause_id,
            title=c.title,
            raw_text=c.raw_text,
            summary=c.summary,
            risk_level=c.risk_level,
            risk_score=c.risk_score,
        )
        db.add(clause)

    # ---------------------------
    # Term 저장
    # ---------------------------
    for t in analysis.terms:
        term = Term(
            document_id=doc.id,
            term=t.term,
            korean=t.korean,
            english=t.english,
            source=t.source,
        )
        db.add(term)

    db.commit()
    return doc


# ======================================================================================
# 3) 문서 리스트 조회
# ======================================================================================
def list_documents(db: Session, user_id: int) -> List[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .all()
    )


# ======================================================================================
# 4) 문서 상세 조회
# ======================================================================================
def get_document(db: Session, document_id: int, user_id: Optional[int] = None) -> Optional[Document]:
    q = db.query(Document).filter(Document.id == document_id)
    if user_id:
        q = q.filter(Document.user_id == user_id)
    return q.first()


def get_document_clauses(db: Session, document_id: int) -> List[Clause]:
    return db.query(Clause).filter(Clause.document_id == document_id).all()


def get_document_terms(db: Session, document_id: int) -> List[Term]:
    return db.query(Term).filter(Term.document_id == document_id).all()


# ======================================================================================
# 5) 문서 + 조항 + 용어 삭제
# ======================================================================================
def delete_document(db: Session, document_id: int, user_id: Optional[int] = None) -> bool:
    q = db.query(Document).filter(Document.id == document_id)
    if user_id:
        q = q.filter(Document.user_id == user_id)

    doc = q.first()
    if not doc:
        return False

    db.query(Clause).filter(Clause.document_id == document_id).delete()
    db.query(Term).filter(Term.document_id == document_id).delete()

    db.delete(doc)
    db.commit()
    return True
