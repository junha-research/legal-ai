# backend/app/core/cache.py

import hashlib
import time
from typing import Any, Optional


class InMemoryCache:
    def __init__(self, default_ttl: int = 60 * 10):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    def make_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < now:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + (ttl or self._default_ttl)
        self._store[key] = (expires_at, value)


# 계약 문서 분석용 캐시 인스턴스
contract_cache = InMemoryCache(default_ttl=60 * 5)
