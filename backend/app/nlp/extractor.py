# backend/app/nlp/extractor.py

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.utils.text_cleaner import normalize_whitespace


@dataclass
class Clause:
    clause_id: str
    title: Optional[str]
    raw_text: str


@dataclass
class NLPInfo:
    clauses: List[Clause] = field(default_factory=list)
    language: str = "ko"
    domain_tags: List[str] = field(default_factory=list)
    parties: List[str] = field(default_factory=list)
    candidate_terms: List[str] = field(default_factory=list)
# -----------------------------------------
# 0) Konlpy(Okt) Lazy Loader 추가
# -----------------------------------------
_okt = None

def get_okt():
    global _okt

    if _okt is None:
        import jpype
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[])

        from konlpy.tag import Okt
        _okt = Okt()

    return _okt

# ---------------------------------------------------------
# 1) 언어 추론
# ---------------------------------------------------------
def _guess_language(text: str) -> str:
    ko = len(re.findall(r"[가-힣]", text))
    en = len(re.findall(r"[A-Za-z]", text))
    if ko > 0 and en > 0:
        return "vie"
    if ko > 0:
        return "ko"
    if en > 0:
        return "en"
    return "ko"


# ---------------------------------------------------------
# 2) 조항 스플릿
# ---------------------------------------------------------
def _split_clauses(text: str) -> List[Clause]:
    text = normalize_whitespace(text)

    pattern = re.compile(r"(제\s*\d+\s*조[^\n]*)", re.MULTILINE)
    matches = list(pattern.finditer(text))

    # 패턴이 없으면 문단 단위로 fallback
    if not matches:
        chunks = re.split(r"\n\s*\n", text)
        clauses = []
        for idx, chunk in enumerate(chunks, start=1):
            cl_text = chunk.strip()
            if not cl_text:
                continue
            clauses.append(
                Clause(
                    clause_id=f"clause_{idx}",
                    title=None,
                    raw_text=cl_text,
                )
            )
        return clauses

    clauses = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        header = match.group(1).strip()
        body = text[start:end].strip()

        title_match = re.search(r"\(([^)]+)\)", header)
        title = title_match.group(1).strip() if title_match else None

        clause_id_match = re.search(r"제\s*(\d+)\s*조", header)
        clause_id = f"제{clause_id_match.group(1)}조" if clause_id_match else f"clause_{i+1}"

        clauses.append(
            Clause(
                clause_id=clause_id,
                title=title,
                raw_text=body,
            )
        )

    return clauses


# ---------------------------------------------------------
# 3) 도메인 태그 추론
# ---------------------------------------------------------
def _guess_domain_tags(text: str) -> List[str]:
    tags = []
    lower = text.lower()
    ko = text

    if any(k in ko for k in ["근로자", "사용자", "퇴직", "임금", "급여", "노동", "고용"]):
        tags.append("고용/근로계약")
    if any(k in ko for k in ["임대인", "임차인", "보증금", "월세", "전세", "임대차"]):
        tags.append("부동산/임대차")
    if any(k in ko for k in ["비밀유지", "기밀", "영업비밀"]):
        tags.append("비밀유지/NDA")
    if any(k in lower for k in ["service", "saas", "cloud"]):
        tags.append("IT/서비스이용계약")
    if any(k in ko for k in ["매도인", "매수인", "대금", "납부", "대금지급"]):
        tags.append("매매/용역계약")
    if not tags:
        tags.append("일반계약")

    return sorted(set(tags))


# ---------------------------------------------------------
# 4) 당사자 추출
# ---------------------------------------------------------
def _guess_parties(text: str) -> List[str]:
    parties = []
    if "근로자" in text: parties.append("근로자")
    if "사용자" in text: parties.append("사용자")
    if "매도인" in text: parties.append("매도인")
    if "매수인" in text: parties.append("매수인")
    if "임대인" in text: parties.append("임대인")
    if "임차인" in text: parties.append("임차인")
    return sorted(set(parties))


# ---------------------------------------------------------
# 5) 후보 용어 추출 (Konlpy 제거 → 정규식 기반 간단 명사 추출)
# ---------------------------------------------------------
def _extract_candidate_terms(text: str) -> List[str]:
    # 한글 2글자 이상 단어만 추출
    words = re.findall(r"[가-힣]{2,}", text)
    words = sorted(set(words))

    # 불용어 제거
    stopwords = {...}

    clean_words = [w for w in words if w not in stopwords]
    return clean_words[:30]

# ---------------------------------------------------------
# 6) NLPInfo 구성함수
# ---------------------------------------------------------
def build_nlp_info(
    text: str,
    language_hint: Optional[str] = None,
    force_language: Optional[str] = None
) -> NLPInfo:
    text_norm = normalize_whitespace(text)

    # 1️⃣ 사용자가 언어를 직접 지정했다면 → 무조건 그걸 우선한다
    if force_language:
        language = force_language
    else:
        # 2️⃣ 아니면 language_hint > 자동 언어추론 순서
        language = language_hint or _guess_language(text_norm)

    clauses = _split_clauses(text_norm)
    domain_tags = _guess_domain_tags(text_norm)
    parties = _guess_parties(text_norm)
    candidate_terms = _extract_candidate_terms(text_norm)

    return NLPInfo(
        clauses=clauses,
        language=language,
        domain_tags=domain_tags,
        parties=parties,
        candidate_terms=candidate_terms,
    )
