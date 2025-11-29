# backend/app/services/llm_prompt.py

import json
from typing import Dict

from app.models.legal import TermDefinition
from app.nlp.extractor import NLPInfo

LANG_PROMPT = {
    "ko": " JSON value는 반드시 한국어로 작성하십시오. JSON key는 절대 번역하거나 변경하지 마십시오.",
    "en": " Write all JSON values in English. Do NOT translate or modify JSON keys.",
    "vi": " Viết toàn bộ giá trị JSON bằng tiếng Việt. KHÔNG dịch hoặc thay đổi các key JSON.",
}

def build_contract_analysis_prompt(
    original_text: str,
    nlp_info: NLPInfo,
    term_definitions: Dict[str, TermDefinition],
    output_language: str = "ko",   # 추가
) -> str:

    # 조항: 최대 10개, 각 원문은 500자까지만 잘라서 전달
    clauses_payload = [
        {
            "clause_id": c.clause_id,
            "title": c.title,
            "raw_text": c.raw_text[:500],
        }
        for c in nlp_info.clauses[:10]
    ]

    # 용어 정의: 최대 30개만 사용
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
        "terms": terms_payload[:30],
    }

    schema_description = {
        "document_id": "string, 예: 'auto_generated_1'",
        "meta": {
            "language": "ko/en/mixed 중 하나",
            "domain_tags": ["문서의 주요 도메인 태그 리스트"],
            "parties": ["근로자, 사용자, 매도인, 매수인 등"],
            "governing_law": "예: '대한민국 법'",
        },
        "summary": {
            "title": "문서 제목 또는 간단한 이름",
            "overall_summary": "문서 전체를 3~5문장 정도로 설명 (200자 이내)",
            "one_line_summary": "핵심만 1문장으로 요약 (80자 이내)",
            "key_points": ["핵심 포인트 bullet 리스트 (최대 2개)"],
            "main_risks": ["중요 위험 요소 bullet 리스트 (최대 2개)"],
            "main_protections": ["중요 보호 장치 bullet 리스트 (최대 2개)"],
            "recommended_actions": ["실무 담당자가 취해야 할 액션 bullet 리스트 (최대 2개)"],
        },
        "risk_profile": {
            "overall_risk_level": "낮음/중간/높음/치명적 중 하나",
            "overall_risk_score": "0~100 정수",
            "risk_dimensions": {
                "지급/대금": "0~100 정수",
                "해지/갱신": "0~100 정수",
                "위약금/손해배상": "0~100 정수",
                "책임/면책": "0~100 정수",
            },
            "comments": "전반적인 리스크에 대한 설명 (200자 이내)",
        },
        "clauses": [
            {
                "clause_id": "조항 ID",
                "title": "조항 제목 (있으면)",
                "raw_text": "조항 원문",
                "summary": "조항 요약 (1~2문장, 150자 이내)",
                "risk_level": "낮음/중간/높음/치명적",
                "risk_score": "0~100 정수",
                "risk_factors": ["위험 요인 리스트 (최대 2개)"],
                "protections": ["보호 장치 리스트 (최대 2개)"],
                "red_flags": ["특히 위험한 포인트 (최대 2개)"],
                "action_guides": ["이 조항 관련 실무 행동 가이드 (최대 2개)"],
                "key_points": ["핵심 포인트 (최대 2개)"],
                "tags": {
                    "domain": ["도메인 태그 (최대 2개)"],
                    "risk": ["리스크 태그 (최대 2개)"],
                    "parties": ["관련 당사자 (최대 3명)"],
                },
            }
        ],
        "causal_graph": [
            {
                "from_clause_id": "원인 조항 ID",
                "to_clause_id": "결과 조항 ID",
                "relationship": "triggers/depends_on/conflicts_with/clarifies/overrides",
                "description": "관계 설명 (1문장, 100자 이내)",
            }
        ],
        "terms": [
            {
                "term": "용어",
                "korean": "쉬운 한국어 설명 (3줄 이내, 150자 이내)",
                "english": "영문(있으면)",
                "source": "출처",
            }
        ],
    }
    lang_instruction = LANG_PROMPT.get(
    output_language,
    LANG_PROMPT["ko"]
)
    prompt = f"""
당신은 한국 계약서·법률 문서를 분석하는 시니어 변호사입니다.
사전 분석 데이터를 참고하여 아래 스키마대로 정확한 JSON만 출력하십시오.

{lang_instruction}

‼ 절대 JSON 외의 텍스트를 출력하지 마세요.
‼ 설명 문장, 마크다운, 코드블록, 주석, 자연어 해설 일체 금지.
‼ JSON 앞뒤에 공백/텍스트/기호 포함 금지. 중괄호 {{ 로 시작해서 }} 로 끝나야 합니다.
⚠️ 언어 규칙:
- Output language for summary/clauses/etc MUST follow: {output_language}.
- BUT risk_level values MUST ALWAYS stay in Korean.
- Use ONLY: "낮음", "중간", "높음", "치명적".
- Never output "low", "medium", "high", "critical", "intermediate".
⚠️ JSON 생성 시 주의:
- JSON이 너무 길어지면 구조가 깨지므로 **모든 필드의 텍스트를 짧게** 작성하십시오.
- 각 문자열 필드는 200자를 넘지 않게 하십시오.
- 리스트는 최대 2개 항목까지만 생성하십시오.
- 필요 없는 필드는 생략하지 말고, 빈 배열 [] 또는 빈 문자열 ""로 채우십시오.
- clauses는 최대 10개까지만 생성하십시오.

[사전 분석 정보(JSON)]:
{json.dumps(pre_analysis, ensure_ascii=False, indent=2)}

[반환 JSON 스키마 설명]:
{json.dumps(schema_description, ensure_ascii=False, indent=2)}

⚠️ 출력 규칙 (반드시 지킬 것):
- JSON만 출력 (문장/설명/마크다운 금지)
- 코드블록( ``` ) 사용 금지
- JSON 외 문자가 1개라도 있으면 안 됨
- 모든 텍스트 필드는 200자 이하
- 리스트 항목은 최대 2개까지만
- clauses는 최대 10개까지만
- JSON 전체는 2500 tokens 이하로 생성

🔥 중요:
- 최종 출력은 반드시 유효한 JSON이어야 합니다.
- JSON은 반드시 여는 중괄호 {{ 로 시작하여 닫는 중괄호 }} 로 끝나야 합니다.
- 만약 일부 정보를 채울 수 없으면 빈 문자열 "" 또는 빈 배열 []을 사용하십시오.
"""


    return prompt
