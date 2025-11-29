# backend/app/db/legal.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

# =========================
# 📌 Clause 테이블
# =========================
class Clause(Base):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    clause_id = Column(String(50), nullable=True)   # "제1조", "clause_1"
    title = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    risk_level = Column(String(20), nullable=True)
    risk_score = Column(Integer, nullable=True)

    # Document 관계
    document = relationship("Document", back_populates="clauses")


# =========================
# 📌 Term 테이블
# =========================
class Term(Base):
    __tablename__ = "terms"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    term = Column(String(255), nullable=False)
    korean = Column(Text, nullable=True)
    english = Column(Text, nullable=True)
    source = Column(String(50), nullable=True, default="MOLEG")

    # Document 관계
    document = relationship("Document", back_populates="terms")
