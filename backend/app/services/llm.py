from __future__ import annotations

import asyncio
import json
from typing import Dict, Any
from app.core.logger import logger

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


# ----------------------------------------------------------
# Gemini 설정
# ----------------------------------------------------------
genai.configure(api_key=settings.GEMINI_API_KEY)
_MODEL_NAME = "gemini-2.5-flash"


def _get_model():
    return genai.GenerativeModel(_MODEL_NAME)


# ----------------------------------------------------------
# Streaming 응답 처리
# ----------------------------------------------------------
async def _stream_llm_text(prompt: str) -> str:
    model = _get_model()

    response = model.generate_content(
        prompt,
        stream=True,
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "max_output_tokens": 24000,
        },
    )

    chunks: list[str] = []

    for chunk in response:   # sync generator
        if hasattr(chunk, "text") and chunk.text:
            chunks.append(chunk.text)

    return "".join(chunks)


# ----------------------------------------------------------
# 코드블록 제거 및 JSON 위치 보정
# ----------------------------------------------------------
def _strip_to_json(text: str) -> str:
    if not text:
        return ""

    t = text.strip()

    if t.startswith("```"):
        t = t.lstrip("`").lstrip()
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    if t.endswith("```"):
        t = t[:-3]

    first = t.find("{")
    if first != -1:
        t = t[first:]
    return t.strip()


# ----------------------------------------------------------
# JSON 자동 복원기
# ----------------------------------------------------------
def _repair_json(json_text: str) -> str:
    if not json_text:
        return json_text

    s = json_text.strip()

    try:
        json.loads(s)
        return s
    except:
        pass

    last = s.rfind("}")
    if last != -1:
        candidate = s[: last + 1]
        try:
            json.loads(candidate)
            return candidate
        except:
            s = candidate

    for _ in range(3):
        replaced = (
            s.replace(", }", "}")
             .replace(", ]", "]")
             .replace(",\n}", "}")
        )
        if replaced == s:
            break

        s = replaced
        try:
            json.loads(s)
            return s
        except:
            continue

    opens = s.count("{")
    closes = s.count("}")
    if opens > closes:
        s += "}" * (opens - closes)
        try:
            json.loads(s)
            return s
        except:
            pass

    return json_text


# ----------------------------------------------------------
# ★ NEW: 영어/베트남어 리스크레벨 자동 변환 매핑
# ----------------------------------------------------------
RISK_LEVEL_MAP = {
    "low": "낮음",
    "medium": "중간",
    "moderate": "중간",
    "high": "높음",
    "critical": "치명적",
    "severe": "치명적",

    # Vietnamese
    "thấp": "낮음",
    "trung bình": "중간",
    "cao": "높음",
    "nghiêm trọng": "치명적"
}


# ----------------------------------------------------------
# DocumentResult 객체 파싱 (안정화 버전)
# ----------------------------------------------------------
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

    # ------------------ 수정된 부분 START ---------------------
    risk_raw = data.get("risk_profile", {}) or {}

    def _to_int(x):
        try:
            return int(float(x))
        except Exception:
            return 0

    raw_level = (risk_raw.get("overall_risk_level", "중간") or "").lower()
    mapped_level = RISK_LEVEL_MAP.get(raw_level, raw_level)

    dims_raw = risk_raw.get("risk_dimensions", {}) or {}
    fixed_dims = {k: _to_int(v) for k, v in dims_raw.items()}

    risk_profile = DocumentRiskProfile(
        overall_risk_level=mapped_level,
        overall_risk_score=_to_int(risk_raw.get("overall_risk_score", 50)),
        risk_dimensions=fixed_dims,
        comments=risk_raw.get("comments", ""),
    )
    # ------------------ 수정된 부분 END ---------------------

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
                risk_score=_to_int(c.get("risk_score", 50)),
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
        causal_out.append(
            ClauseCausality(
                from_clause_id=rel.get("from_clause_id", ""),
                to_clause_id=rel.get("to_clause_id", ""),
                relationship=rel.get("relationship", "depends_on"),
                description=rel.get("description", ""),
            )
        )

    terms_out = []
    for t in data.get("terms", []) or []:
        terms_out.append(
            TermDefinition(
                term=t.get("term", ""),
                korean=t.get("korean", ""),
                english=t.get("english"),
                source=t.get("source", "MOLEG/LLM"),
            )
        )

    return DocumentResult(
        document_id=data.get("document_id", "auto_generated"),
        meta=meta,
        summary=summary,
        risk_profile=risk_profile,
        clauses=clauses_out,
        causal_graph=causal_out,
        terms=terms_out,
    )


# ----------------------------------------------------------
# 메인 계약서 분석 함수
# ----------------------------------------------------------
async def analyze_contract(
    original_text: str,
    nlp_info: NLPInfo,
    term_definitions: Dict[str, TermDefinition],
    output_language: str = "ko",   
) -> DocumentResult:

    cache_key = contract_cache.make_key(original_text + nlp_info.language)
    cached = contract_cache.get(cache_key)
    if cached:
        return cached

    prompt = build_contract_analysis_prompt(
    original_text,
    nlp_info,
    term_definitions,
    output_language  # 추가
)

    raw_text = await _stream_llm_text(prompt)

    print("\n=============== RAW TEXT BEFORE PARSE ===============")
    print(raw_text)
    print("=====================================================\n")

    json_text = _strip_to_json(raw_text)
    json_text = _repair_json(json_text)

    data = None
    try:
        data = json.loads(json_text)
    except:
        pass

    if data is None:
        last = json_text.rfind("}")
        if last != -1:
            try:
                data = json.loads(json_text[: last + 1])
            except:
                pass

    if data is None:
        print("❌ JSON 파싱 실패 → fallback 사용")
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
                "comments": "LLM 응답 파싱 오류.",
            },
            "clauses": [],
            "causal_graph": [],
            "terms": [],
        }

    result = _safe_parse_document_result(data)
    contract_cache.set(cache_key, result)
    return result


# ----------------------------------------------------------
# 다국어 법률 Q&A
# ----------------------------------------------------------
LANGUAGE_PROMPTS = {
    "ko": {
        "system": "당신은 한국 법률 전문가입니다.",
        "sections": {
            "summary": "한줄 요약",
            "explanation": "쉬운말 설명",
            "key_points": "핵심 포인트",
            "risks": "위험 요소",
            "protections": "보호 장치",
            "actions": "권장 행동",
            "terms": "법령 용어 정의",
            "laws": "관련 법령",
            "analysis": "조항별 상세 분석",
        }
    },
    "en": {
        "system": "You are a legal expert.",
        "sections": {
            "summary": "Summary",
            "explanation": "Simple Explanation",
            "key_points": "Key Points",
            "risks": "Risk Factors",
            "protections": "Legal Protections",
            "actions": "Recommended Actions",
            "terms": "Legal Terms",
            "laws": "Related Laws",
            "analysis": "Detailed Analysis",
        }
    },
    "vi": {
        "system": "Bạn là chuyên gia pháp lý.",
        "sections": {
            "summary": "Tóm tắt",
            "explanation": "Giải thích đơn giản",
            "key_points": "Điểm chính",
            "risks": "Yếu tố rủi ro",
            "protections": "Bảo vệ pháp lý",
            "actions": "Hành động được đề xuất",
            "terms": "Thuật ngữ pháp lý",
            "laws": "Luật liên quan",
            "analysis": "Phân tích chi tiết",
        }
    }
}


async def generate_legal_answer_multilang(question: str, language: str = "ko") -> str:

    lang_config = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["ko"])
    sections = lang_config["sections"]

    prompt = f"""
{lang_config["system"]} Answer the following question in {language.upper()} language.

Question: {question}

**Format (Markdown):**

## {sections["summary"]}
[One sentence summary]

## {sections["explanation"]}
[Easy-to-understand explanation]

## {sections["key_points"]}
- [Point 1]
- [Point 2]
- [Point 3]

## {sections["risks"]}
[Legal risks to be aware of]

## {sections["protections"]}
[Legal protections and rights]

## {sections["actions"]}
1. [Action 1]
2. [Action 2]
3. [Action 3]

## {sections["terms"]}
- **Term1**: Definition
- **Term2**: Definition

## {sections["laws"]}
- [Law name](link)
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"❌ LLM 답변 생성 실패: {e}")
        error_messages = {
            "ko": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
            "en": f"Error generating answer: {str(e)}",
            "vi": f"Lỗi khi tạo câu trả lời: {str(e)}"
        }
        return error_messages.get(language, error_messages["ko"])
