# backend/app/services/law_api.py

import asyncio
import json
from typing import Dict, List, Optional

import aiohttp

from app.core.config import settings
from app.models.legal import TermDefinition


BASE_URL = "http://www.law.go.kr/DRF/lawService.do"


async def _fetch_single_term(session: aiohttp.ClientSession, term: str) -> Optional[TermDefinition]:
    if not settings.MOLEG_API_KEY:
        return None

    params = {
        "OC": settings.MOLEG_API_KEY,
        "target": "lstrm",
        "query": term,
        "type": "JSON",
    }

    try:
        async with session.get(BASE_URL, params=params, timeout=5) as resp:
            if resp.status != 200:
                return None

            try:
                data = await resp.json(content_type=None)
            except Exception:
                # 응답이 깨지는 경우 텍스트로 확인 후 패스
                _ = await resp.text()
                return None

            service = data.get("LsTrmService")
            if not service:
                return None

            defs = service.get("법령용어정의")
            codes = service.get("법령용어코드명")

            if not codes:
                return None

            # 단일/복수 케이스 통일
            if isinstance(codes, str):
                codes = [codes]
                defs = [defs] if isinstance(defs, str) else [defs or ""]

            korean_def = None
            english_def = None

            for code, definition in zip(codes, defs):
                if code == "법령한영사전":
                    english_def = (definition or "").strip()
                elif not korean_def:
                    korean_def = (definition or "").strip()

            if not korean_def:
                return None

            return TermDefinition(term=term, korean=korean_def, english=english_def)

    except Exception:
        return None


async def fetch_term_definitions(terms: List[str]) -> Dict[str, TermDefinition]:
    """
    여러 용어를 병렬로 조회해서 term -> TermDefinition 매핑으로 리턴.
    """
    if not settings.MOLEG_API_KEY:
        return {}

    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_single_term(session, t) for t in terms]
        results = await asyncio.gather(*tasks)

    term_map: Dict[str, TermDefinition] = {}
    for t, r in zip(terms, results):
        if r:
            term_map[t] = r
    return term_map
