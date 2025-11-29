# backend/app/models/legal.py
from __future__ import annotations

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


# =========================
# 📌 공통 타입
# =========================
RiskLevel = Literal["낮음", "중간", "높음", "치명적"]


# =========================
# 📌 용어 정의
# =========================
class TermDefinition(BaseModel):
    term: str
    korean: str = Field(..., description="법제처 등에서 가져온 한국어 정의")
    english: Optional[str] = Field(None, description="영문 정의 (있으면)")
    source: str = Field("MOLEG", description="정의 출처 (MOLEG 등)")


# =========================
# 📌 조항 태그
# =========================
class ClauseTags(BaseModel):
    domain: List[str] = Field(default_factory=list, description="도메인 태그 (고용, 임대차, NDA 등)")
    risk: List[str] = Field(default_factory=list, description="리스크 유형 (지연이행, 해지, 위약금 등)")
    parties: List[str] = Field(default_factory=list, description="당사자 구분 (근로자, 사용자, 매도인 등)")


# =========================
# 📌 조항 분석 결과
# =========================
class ClauseResult(BaseModel):
    clause_id: str = Field(..., description="조항 ID (예: '제7조' 또는 'clause_1')")
    title: Optional[str] = Field(None, description="조항 제목 (있으면)")
    raw_text: str = Field(..., description="조항 원문 전체")
    summary: str = Field(..., description="조항 요약")

    risk_level: RiskLevel
    risk_score: int = Field(..., ge=0, le=100, description="0~100 점수")
    risk_factors: List[str] = Field(default_factory=list)
    protections: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

    action_guides: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)

    tags: ClauseTags = Field(default_factory=ClauseTags)


# =========================
# 📌 조항 간 인과관계
# =========================
class ClauseCausality(BaseModel):
    from_clause_id: str
    to_clause_id: str
    relationship: Literal[
        "triggers", "depends_on", "conflicts_with", "clarifies", "overrides"
    ]
    description: str


# =========================
# 📌 문서 요약 섹션
# =========================
class DocumentSummary(BaseModel):
    title: Optional[str] = None
    overall_summary: str
    one_line_summary: str
    key_points: List[str] = Field(default_factory=list)
    main_risks: List[str] = Field(default_factory=list)
    main_protections: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


# =========================
# 📌 문서 메타 정보
# =========================
class DocumentMeta(BaseModel):
    language: Literal["ko", "en", "vie"] = "ko"
    domain_tags: List[str] = Field(default_factory=list)
    parties: List[str] = Field(default_factory=list)
    governing_law: Optional[str] = None


# =========================
# 📌 문서 리스크 프로필
# =========================
class DocumentRiskProfile(BaseModel):
    overall_risk_level: RiskLevel
    overall_risk_score: int = Field(..., ge=0, le=100)
    risk_dimensions: Dict[str, int] = Field(default_factory=dict)
    comments: str = ""


# =========================
# 📌 최종 문서 분석 결과
# =========================
class DocumentResult(BaseModel):
    document_id: Optional[str] = None

    meta: DocumentMeta
    summary: DocumentSummary
    risk_profile: DocumentRiskProfile
    clauses: List[ClauseResult]
    causal_graph: List[ClauseCausality] = Field(default_factory=list)
    terms: List[TermDefinition] = Field(default_factory=list)
