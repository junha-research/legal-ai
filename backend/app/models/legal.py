# backend/app/models/legal.py

from __future__ import annotations

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


RiskLevel = Literal["낮음", "중간", "높음", "치명적"]


class TermDefinition(BaseModel):
    term: str
    korean: str = Field(..., description="법제처 등에서 가져온 한국어 정의")
    english: Optional[str] = Field(None, description="영문 정의 (있으면)")
    source: str = Field("MOLEG", description="정의 출처 (MOLEG 등)")


class ClauseTags(BaseModel):
    domain: List[str] = Field(default_factory=list, description="도메인 태그 (고용, 임대차, NDA 등)")
    risk: List[str] = Field(default_factory=list, description="리스크 유형 (지연이행, 해지, 위약금 등)")
    parties: List[str] = Field(default_factory=list, description="당사자 구분 (근로자, 사용자, 매도인 등)")


class ClauseResult(BaseModel):
    clause_id: str = Field(..., description="조항 ID (예: '제7조' 또는 'clause_1')")
    title: Optional[str] = Field(None, description="조항 제목 (있으면)")
    raw_text: str = Field(..., description="조항 원문 전체")
    summary: str = Field(..., description="조항 요약")

    risk_level: RiskLevel
    risk_score: int = Field(..., ge=0, le=100, description="0~100 점수")
    risk_factors: List[str] = Field(default_factory=list, description="위험 요인 리스트")
    protections: List[str] = Field(default_factory=list, description="계약상 보호 장치")
    red_flags: List[str] = Field(default_factory=list, description="치명적/주의해야 할 포인트")

    action_guides: List[str] = Field(
        default_factory=list, description="실무 행동 가이드 (협상 시 확인/수정 포인트)"
    )
    key_points: List[str] = Field(default_factory=list, description="핵심 포인트 (bullet 형태)")
    tags: ClauseTags = Field(default_factory=ClauseTags)


class ClauseCausality(BaseModel):
    from_clause_id: str = Field(..., description="원인/선행 조항 ID")
    to_clause_id: str = Field(..., description="결과/후행 조항 ID")
    relationship: Literal[
        "triggers", "depends_on", "conflicts_with", "clarifies", "overrides"
    ] = Field(..., description="조항 간 관계 유형")
    description: str = Field(..., description="자연어로 관계 설명")


class DocumentSummary(BaseModel):
    title: Optional[str] = None
    overall_summary: str
    one_line_summary: str
    key_points: List[str] = Field(default_factory=list)
    main_risks: List[str] = Field(default_factory=list)
    main_protections: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class DocumentMeta(BaseModel):
    language: Literal["ko", "en", "mixed"] = "ko"
    domain_tags: List[str] = Field(default_factory=list)
    parties: List[str] = Field(default_factory=list)
    governing_law: Optional[str] = None


class DocumentRiskProfile(BaseModel):
    overall_risk_level: RiskLevel
    overall_risk_score: int = Field(..., ge=0, le=100)
    risk_dimensions: Dict[str, int] = Field(
        default_factory=dict,
        description="리스크 카테고리별 점수 예) {'지급/대금': 80, '해지': 60}",
    )
    comments: str = Field("", description="전반적인 리스크 코멘트")


class DocumentResult(BaseModel):
    document_id: str
    meta: DocumentMeta
    summary: DocumentSummary
    risk_profile: DocumentRiskProfile
    clauses: List[ClauseResult]
    causal_graph: List[ClauseCausality]
    terms: List[TermDefinition]
