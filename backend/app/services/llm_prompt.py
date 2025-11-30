# backend/app/services/llm_prompt.py

import json
from typing import Dict
from app.models.legal import TermDefinition
from app.nlp.extractor import NLPInfo

# -----------------------------------------
# 언어별 값 생성 규칙 (summary, clauses, terms 등)
# -----------------------------------------
LANG_VALUE_RULE = {
    "ko": "- 모든 value는 반드시 한국어로 작성하십시오.",
    "en": "- All JSON values must be written in English, EXCEPT risk_level (Korean only).",
    "vi": "- Tất cả giá trị JSON phải được viết bằng tiếng Việt, TRỪ risk_level (chỉ tiếng Hàn).",
}

# -----------------------------------------
# 언어별 설명 문구 (summary, clauses 생성용)
# -----------------------------------------
LANG_PROMPT = {
    "ko": "📌 출력 언어: 한국어로 작성하십시오.",
    "en": "📌 Output Language: Write all JSON values in English **except risk_level** which must be Korean.",
    "vi": "📌 Ngôn ngữ xuất: Viết tất cả giá trị JSON bằng tiếng Việt, **ngoại trừ risk_level** phải bằng tiếng Hàn.",
}


def build_contract_analysis_prompt(
    original_text: str,
    nlp_info: NLPInfo,
    term_definitions: Dict[str, TermDefinition],
    output_language: str = "ko",
) -> str:
    """
    계약서 분석 LLM 프롬프트 생성기
    """

    # 언어 규칙 불러오기
    lang_value_rule = LANG_VALUE_RULE.get(output_language, LANG_VALUE_RULE["ko"])
    lang_instruction = LANG_PROMPT.get(output_language, LANG_PROMPT["ko"])

    # -----------------------------------------
    # risk_level은 어떤 언어에서도 반드시 한국어 고정
    # -----------------------------------------
    risk_level_rule = """
⚠️ risk_level 필드는 어떤 언어 모드에서도 반드시 다음 네 가지 중 하나만 사용하십시오:
- '낮음'
- '중간'
- '높음'
- '치명적'

영어/베트남어 출력 모드에서도 risk_level 값은 절대로 'Low', 'Medium', 'High', 'Critical' 등 영어 단어를 사용하지 마십시오.
"""

    # -----------------------------------------
    # 조항/용어 사전 분석 정보
    # -----------------------------------------
    clauses_payload = [
        {
            "clause_id": c.clause_id,
            "title": c.title,
            "raw_text": c.raw_text[:500],
        }
        for c in nlp_info.clauses[:10]
    ]

    terms_payload = [
        {
            "term": t.term,
            "korean": t.korean,
            "english": t.english,
            "source": t.source,
        }
        for t in term_definitions.values()
    ][:30]

    pre_analysis = {
        "language": nlp_info.language,
        "domain_tags_hint": nlp_info.domain_tags,
        "parties_hint": nlp_info.parties,
        "clauses": clauses_payload,
        "terms": terms_payload,
    }

    # -----------------------------------------
    # 출력 JSON 스키마
    # -----------------------------------------
    schema_description = {
        "document_id": "string, 예: 'auto_generated_1'",
        "meta": {
            "language": "ko/en/mixed 중 하나",
            "domain_tags": ["문서의 주요 도메인 태그 리스트"],
            "parties": ["근로자, 사용자, 매도인, 매수인 등"],
            "governing_law": "예: '대한민국 법'",
        },
        "summary": {
            "title": "문서 제목",
            "overall_summary": "문서 전체 요약 (3~5문장)",
            "one_line_summary": "핵심 한 문장 요약",
            "key_points": ["핵심 포인트 2개 이상"],
            "main_risks": ["위험 요소 2개 이상"],
            "main_protections": ["보호 요소 2개 이상"],
            "recommended_actions": ["실행 가이드 2개 이상"],
        },
        "risk_profile": {
            "overall_risk_level": "낮음/중간/높음/치명적 중 하나",
            "overall_risk_score": "0~100",
            "risk_dimensions": {
                "지급/대금": "0~100",
                "해지/갱신": "0~100",
                "위약금/손해배상": "0~100",
                "책임/면책": "0~100",
            },
            "comments": "200자 이내 설명",
        },
        "clauses": [
            {
                "clause_id": "조항 ID",
                "title": "조항 제목",
                "raw_text": "원문",
                "summary": "1~2 문장 요약",
                "risk_level": "낮음/중간/높음/치명적",
                "risk_score": "0~100",
                "risk_factors": ["1개 이상"],
                "protections": ["1개 이상"],
                "red_flags": ["1개 이상"],
                "action_guides": ["1개 이상"],
                "key_points": ["1개 이상"],
                "tags": {
                    "domain": ["태그"],
                    "risk": ["태그"],
                    "parties": ["당사자"],
                },
            }
        ],
        "causal_graph": [
            {
                "from_clause_id": "조항 ID",
                "to_clause_id": "조항 ID",
                "relationship": "triggers/depends_on/conflicts_with/clarifies",
                "description": "관계 설명",
            }
        ],
        "terms": [
            {
                "term": "용어",
                "korean": "설명",
                "english": "영문 (있으면)",
                "source": "출처",
            }
        ],
    }

    # -----------------------------------------
    # 최종 LLM Prompt
    # -----------------------------------------
    prompt = f"""
당신은 한국·영문 계약서를 분석하는 시니어 변호사입니다.
입력된 원문이 매우 짧거나 간단해도 아래 스키마 전체를 **완전히 채운 풍부한 JSON**을 생성해야 합니다.

===============================
📌 언어 규칙
===============================
{lang_instruction}

{lang_value_rule}

{risk_level_rule}

===============================
🚫 절대 금지 규칙
===============================
1) "" (빈 문자열) 금지
2) [] (빈 배열) 금지
3) "정보 없음", "해당 없음" 등 금지
4) JSON 외 텍스트 금지
5) Markdown 코드블록 금지
6) 필드 누락 금지

===============================
📌 생성 규칙
===============================
- clauses: 최소 5개, 최대 10개
- 모든 배열은 최소 2개 이상
- terms: 최소 3개
- causal_graph: 최소 1개
- summary 섹션의 모든 필드 최소 2개 이상

===============================
📌 사전 분석 정보
===============================
{json.dumps(pre_analysis, ensure_ascii=False, indent=2)}

===============================
📌 출력 JSON 스키마
===============================
{json.dumps(schema_description, ensure_ascii=False, indent=2)}

===============================
🔥 출력 방식
===============================
- JSON만 출력
- 앞뒤로 어떠한 문자도 출력하지 마십시오

"""

    return prompt
