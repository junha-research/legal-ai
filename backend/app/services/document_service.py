# backend/app/services/document_service.py

from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session

# DB 테이블
from app.db.models import Document
from app.db.legal import Clause, Term

# LLM 분석 모델
from app.models.legal import DocumentResult


# ======================================================================================
# 1) 기존 기능: 일반 Q&A 저장
# ======================================================================================

def save_document_from_analysis(
    db: Session,
    user_id: int,
    original_text: str,
    summary: str,
    answer_markdown: str,
):
    """
    🔵 Q&A 저장용 — 간단한 문서 기록
    """
    doc = Document(
        user_id=user_id,
        original_text=original_text,
        summary=summary,
        answer_markdown=answer_markdown,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ======================================================================================
# 2) 신규 기능: 계약서 분석 전체 저장 (Document + Clause + Term)
# ======================================================================================

def save_document(
    db: Session,
    analysis: DocumentResult,
    file_name: str,
    user_id: Optional[int] = None,
):
    """
    🟣 계약서 분석 전체 저장 기능
    Document, Clause, Term 모두 저장
    """

    # ---------------------------
    # Document 저장
    # ---------------------------
    doc = Document(
        user_id=user_id,
        title=analysis.summary.title or file_name,
        original_text="",  # OCR 텍스트가 있으면 여기에 넣을 수 있음
        summary=analysis.summary.overall_summary,
        answer_markdown="",  # 이건 RAG Q&A용이라서 비워둠
        language=analysis.meta.language,
        parties=",".join(analysis.meta.parties),
        domain_tags=",".join(analysis.meta.domain_tags),
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
# 4) 문서 상세 조회 (Document + Clause + Term도 함께 조회 가능)
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
# 5) 문서 삭제 (Document + Clause + Term 모두 삭제)
# ======================================================================================

def delete_document(db: Session, document_id: int, user_id: Optional[int] = None) -> bool:
    # 먼저 문서 가져오기
    q = db.query(Document).filter(Document.id == document_id)
    if user_id:
        q = q.filter(Document.user_id == user_id)

    doc = q.first()
    if not doc:
        return False

    # 자식 데이터 삭제
    db.query(Clause).filter(Clause.document_id == document_id).delete()
    db.query(Term).filter(Term.document_id == document_id).delete()

    # 문서 삭제
    db.delete(doc)
    db.commit()
    return True
