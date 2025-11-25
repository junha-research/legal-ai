# backend/app/services/llm_prompt.py

import json
from typing import Dict, List

from app.models.legal import TermDefinition
from app.nlp.extractor import NLPInfo


def build_contract_analysis_prompt(
    original_text: str,
    nlp_info: NLPInfo,
    term_definitions: Dict[str, TermDefinition],
) -> str:

    clauses_payload = [
        {
            "clause_id": c.clause_id,
            "title": c.title,
            "raw_text": c.raw_text,
        }
        for c in nlp_info.clauses
    ]

    terms_payload = [
        {
            "term": t.term,
            "korean": t.korean,
            "english": t.english,
            "source": t.source,
        }
        for t in term_definitions.values()
    ]

    pre_analysis = {
        "language": nlp_info.language,
        "domain_tags_hint": nlp_info.domain_tags,
        "parties_hint": nlp_info.parties,
        "clauses": clauses_payload,
        "terms": terms_payload,
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
            "overall_summary": "문서 전체를 5~10문장 정도로 설명",
            "one_line_summary": "핵심만 1문장으로 요약",
            "key_points": ["핵심 포인트 bullet 리스트"],
            "main_risks": ["중요 위험 요소 bullet 리스트"],
            "main_protections": ["중요 보호 장치 bullet 리스트"],
            "recommended_actions": ["실무 담당자가 취해야 할 액션 bullet 리스트"],
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
            "comments": "전반적인 리스크에 대한 설명",
        },
        "clauses": [
            {
                "clause_id": "조항 ID",
                "title": "조항 제목 (있으면)",
                "raw_text": "조항 원문",
                "summary": "조항 요약",
                "risk_level": "낮음/중간/높음/치명적",
                "risk_score": "0~100 정수",
                "risk_factors": ["위험 요인 리스트"],
                "protections": ["보호 장치 리스트"],
                "red_flags": ["특히 위험한 포인트"],
                "action_guides": ["이 조항 관련 실무 행동 가이드"],
                "key_points": ["핵심 포인트"],
                "tags": {
                    "domain": ["도메인 태그"],
                    "risk": ["리스크 태그"],
                    "parties": ["관련 당사자"],
                },
            }
        ],
        "causal_graph": [
            {
                "from_clause_id": "원인 조항 ID",
                "to_clause_id": "결과 조항 ID",
                "relationship": "triggers/depends_on/conflicts_with/clarifies/overrides",
                "description": "관계 설명",
            }
        ],
        "terms": [
            {
                "term": "용어",
                "korean": "쉬운 한국어 설명",
                "english": "영문(있으면)",
                "source": "출처",
            }
        ],
    }

    # ---------------------------
    # 🔥 JSON-only 강제 프롬프트
    # ---------------------------
    prompt = f"""
당신은 한국 계약서·법률 문서를 분석하는 시니어 변호사입니다.
사전 분석 데이터를 참고하여 아래 스키마대로 정확한 JSON만 출력하십시오.

‼ 절대 JSON 외의 텍스트를 출력하지 마세요.
‼ 설명 문장, 마크다운, 코드블록, 문장형 해설 일체 금지.
‼ JSON 앞뒤에 공백/텍스트/기호 포함 금지.

[사전 분석 정보(JSON)]:
{json.dumps(pre_analysis, ensure_ascii=False, indent=2)}

반드시 아래 스키마에 맞는 JSON만 출력하십시오:

[반환 JSON 스키마 설명]:
{json.dumps(schema_description, ensure_ascii=False, indent=2)}

⚠️ 출력 규칙:
- JSON만 출력 (문장 금지)
- 마크다운 금지
- 코드블록 금지
- 설명/요약 문장 금지
- JSON 외 문자가 1개라도 있으면 안 됨
- 출력 JSON은 절대 3000 token을 넘지 않는다.
- 각 필드에 너무 긴 문장은 넣지 않는다.
- 용어 정의는 3줄 이내.
- clauses는 최대 10개까지만 추출한다.
"""

    return prompt
