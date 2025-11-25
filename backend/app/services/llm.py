from __future__ import annotations

import asyncio
import json
from typing import Dict, Any

import google.generativeai as genai

from app.core.config import settings
from app.core.cache import contract_cache
from app.models.legal import (
    DocumentResult,
    DocumentMeta,
    DocumentSummary,
    DocumentRiskProfile,
    ClauseResult,
    ClauseTags,
    ClauseCausality,
    TermDefinition,
)
from app.nlp.extractor import NLPInfo
from app.services.llm_prompt import build_contract_analysis_prompt


genai.configure(api_key=settings.GEMINI_API_KEY)

_MODEL_NAME = "gemini-2.0-flash-lite"


def _get_model():
    return genai.GenerativeModel(_MODEL_NAME)


# --------------------------------------------------------
# Gemini 응답에서 JSON 문자열을 안정적으로 추출
# --------------------------------------------------------
def _extract_llm_text(resp: Any) -> str:
    """
    Gemini 응답이 어떤 형태든 JSON 문자열만 최대한 뽑아냄.
    """
    if resp is None:
        return ""

    # 일반적인 응답
    if hasattr(resp, "text") and resp.text:
        return resp.text

    # candidates 구조
    try:
        parts = resp.candidates[0].content.parts
        texts = [p.text for p in parts if hasattr(p, "text")]
        if texts:
            return "\n".join(texts)
    except Exception:
        pass

    # dict일 경우
    if isinstance(resp, dict):
        return json.dumps(resp, ensure_ascii=False)

    return ""


# --------------------------------------------------------
# 코드블록 제거
# --------------------------------------------------------
def _strip_to_json(text: str) -> str:
    t = text.strip()

    if t.startswith("```"):
        t = t.lstrip("`")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()

    # 끝 부분에 ``` 있으면 제거
    if t.endswith("```"):
        t = t[:-3]

    return t.strip()


# --------------------------------------------------------
# DocumentResult 안전 파싱
# --------------------------------------------------------
def _safe_parse_document_result(data: dict) -> DocumentResult:

    meta_raw = data.get("meta", {}) or {}
    meta = DocumentMeta(
        language=meta_raw.get("language", "ko"),
        domain_tags=meta_raw.get("domain_tags", []),
        parties=meta_raw.get("parties", []),
        governing_law=meta_raw.get("governing_law"),
    )

    summary_raw = data.get("summary", {}) or {}
    summary = DocumentSummary(
        title=summary_raw.get("title"),
        overall_summary=summary_raw.get("overall_summary", ""),
        one_line_summary=summary_raw.get("one_line_summary", ""),
        key_points=summary_raw.get("key_points", []) or [],
        main_risks=summary_raw.get("main_risks", []) or [],
        main_protections=summary_raw.get("main_protections", []) or [],
        recommended_actions=summary_raw.get("recommended_actions", []) or [],
    )

    risk_raw = data.get("risk_profile", {}) or {}
    risk_profile = DocumentRiskProfile(
        overall_risk_level=risk_raw.get("overall_risk_level", "중간"),
        overall_risk_score=int(risk_raw.get("overall_risk_score", 50)),
        risk_dimensions=risk_raw.get("risk_dimensions", {}) or {},
        comments=risk_raw.get("comments", ""),
    )

    clauses_out = []
    for c in data.get("clauses", []) or []:
        tags_raw = c.get("tags", {}) or {}
        clauses_out.append(
            ClauseResult(
                clause_id=c.get("clause_id", "unknown"),
                title=c.get("title"),
                raw_text=c.get("raw_text", ""),
                summary=c.get("summary", ""),
                risk_level=c.get("risk_level", "중간"),
                risk_score=int(c.get("risk_score", 50)),
                risk_factors=c.get("risk_factors", []) or [],
                protections=c.get("protections", []) or [],
                red_flags=c.get("red_flags", []) or [],
                action_guides=c.get("action_guides", []) or [],
                key_points=c.get("key_points", []) or [],
                tags=ClauseTags(
                    domain=tags_raw.get("domain", []) or [],
                    risk=tags_raw.get("risk", []) or [],
                    parties=tags_raw.get("parties", []) or [],
                ),
            )
        )

    causal_out = []
    for rel in data.get("causal_graph", []) or []:
        try:
            causal_out.append(
                ClauseCausality(
                    from_clause_id=rel.get("from_clause_id", ""),
                    to_clause_id=rel.get("to_clause_id", ""),
                    relationship=rel.get("relationship", "depends_on"),
                    description=rel.get("description", ""),
                )
            )
        except Exception:
            continue

    terms_out = []
    for t in data.get("terms", []) or []:
        try:
            terms_out.append(
                TermDefinition(
                    term=t.get("term", ""),
                    korean=t.get("korean", ""),
                    english=t.get("english"),
                    source=t.get("source", "MOLEG/LLM"),
                )
            )
        except Exception:
            continue

    return DocumentResult(
        document_id=data.get("document_id", "auto_generated"),
        meta=meta,
        summary=summary,
        risk_profile=risk_profile,
        clauses=clauses_out,
        causal_graph=causal_out,
        terms=terms_out,
    )


# --------------------------------------------------------
# 메인 분석 함수
# --------------------------------------------------------
async def analyze_contract(
    original_text: str,
    nlp_info: NLPInfo,
    term_definitions: Dict[str, TermDefinition],
) -> DocumentResult:

    cache_key = contract_cache.make_key(original_text)
    cached = contract_cache.get(cache_key)
    if cached:
        return cached

    prompt = build_contract_analysis_prompt(original_text, nlp_info, term_definitions)

    model = _get_model()

    # Gemini 호출
    def _call_llm() -> Any:
        try:
            return model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                    "max_output_tokens": 4096,
                },
            )
        except Exception as e:
            print("=== LLM 호출 오류 ===")
            print(e)
            return None

    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(None, _call_llm)

    # 🔥 디버깅: Gemini 원본 응답 출력
    print("\n================ RAW RESP FROM GEMINI =================")
    print(resp)
    print("=======================================================\n")

    raw_text = _extract_llm_text(resp)

    # 🔥 디버깅: 파싱 전 텍스트 출력
    print("=============== RAW TEXT BEFORE PARSE ===============")
    print(raw_text)
    print("=====================================================\n")

    json_text = _strip_to_json(raw_text)

    # JSON 파싱 시도
    try:
        data = json.loads(json_text)
    except Exception:
        print("❌ JSON 파싱 실패 → fallback으로 전환합니다.")

        data = {
            "document_id": "fallback",
            "meta": {
                "language": nlp_info.language,
                "domain_tags": nlp_info.domain_tags,
                "parties": nlp_info.parties,
            },
            "summary": {
                "title": "AI 분석 오류",
                "overall_summary": "LLM 응답 파싱 실패.",
                "one_line_summary": "파싱 오류",
                "key_points": [],
                "main_risks": [],
                "main_protections": [],
                "recommended_actions": [],
            },
            "risk_profile": {
                "overall_risk_level": "중간",
                "overall_risk_score": 50,
                "risk_dimensions": {},
                "comments": "LLM 응답 파싱 오류 발생.",
            },
            "clauses": [],
            "causal_graph": [],
            "terms": [],
        }

    result = _safe_parse_document_result(data)
    contract_cache.set(cache_key, result)

    return result
