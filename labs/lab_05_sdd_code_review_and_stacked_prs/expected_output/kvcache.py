# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compliant bounded FIFO Key-Value Cache with per-entry TTL (REQ-0001..REQ-0006)."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import threading
import time
from typing import Any, Callable, Optional


@dataclass
class _CacheEntry:
    value: Any
    expires_at: Optional[float] = None


class KVCache:
    """Thread-safe bounded FIFO cache with optional per-entry TTL."""

    def __init__(
        self,
        max_size: int = 128,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._clock = clock
        self._lock = threading.RLock()
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()

    def _is_expired(self, entry: _CacheEntry, now: float) -> bool:
        return entry.expires_at is not None and now >= entry.expires_at

    def _purge_expired(self, now: float) -> None:
        expired_keys = [
            k for k, v in self._store.items() if self._is_expired(v, now)
        ]
        for k in expired_keys:
            del self._store[k]

    def _upsert(
        self, key: str, value: Any, expires_at: Optional[float], now: float
    ) -> None:
        self._purge_expired(now)
        if key in self._store:
            self._store[key] = _CacheEntry(value=value, expires_at=expires_at)
            return
        if len(self._store) >= self._max_size:
            self._store.popitem(last=False)
        self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    def put(self, key: str, value: Any) -> None:
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._upsert(key, value, None, self._clock())

    def put_with_ttl(self, key: str, value: Any, ttl_seconds: float) -> None:
        if not key:
            raise ValueError("key must be non-empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        with self._lock:
            now = self._clock()
            self._upsert(key, value, now + ttl_seconds, now)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            now = self._clock()
            entry = self._store.get(key)
            if entry is None:
                return None
            if self._is_expired(entry, now):
                del self._store[key]
                return None
            return entry.value

    def delete(self, key: str) -> bool:
        with self._lock:
            now = self._clock()
            entry = self._store.get(key)
            if entry is None:
                return False
            del self._store[key]
            return not self._is_expired(entry, now)

    def __len__(self) -> int:
        with self._lock:
            self._purge_expired(self._clock())
            return len(self._store)
