# backend/app/db/models.py
"""
기존 User/Document/Conversation 구조 유지
+ 계약서 분석 확장 필드 추가
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

from app.db.legal import Clause, Term

# =========================
# 📌 Document 모델 (확장 적용)
# =========================
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # 기존 필드
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_text = Column(Text, nullable=False)

    title = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    answer_markdown = Column(Text, nullable=True)

    risk_score = Column(Integer, nullable=True)
    user_query = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 신규 계약서 분석 필드
    language = Column(String(20), nullable=True)             # ko/en/vi
    domain_tags = Column(String(255), nullable=True)         # "부동산,근로"
    parties = Column(String(255), nullable=True)             # "임대인,임차인"
    risk_level = Column(String(20), nullable=True)           # 낮음/중간/높음/치명적

    # 관계
    user = relationship("User", back_populates="documents")

    # 🔥 정식 관계 (중복 제거 후 정상버전)
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    terms = relationship("Term", back_populates="document", cascade="all, delete-orphan")
# =========================
# 📌 User 모델
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    open_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(320))
    login_method = Column(String(64))
    role = Column(String(20), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_signed_in = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

    # Document 관계
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")


# =========================
# 📌 Conversation
# =========================
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    status = Column(String(20), default="pending")
    language = Column(String(10), default="ko")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    bookmarks = relationship("Bookmark", back_populates="conversation", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="conversation", cascade="all, delete-orphan")


# =========================
# 📌 Bookmark
# =========================
class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookmarks")
    conversation = relationship("Conversation", back_populates="bookmarks")


# =========================
# 📌 ShareLink
# =========================
class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="share_links")

