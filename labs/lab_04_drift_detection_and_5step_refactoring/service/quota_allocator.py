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

"""Bugged TokenBucketQuotaAllocator exhibiting REQ-0005 timestamp drift."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Callable


@dataclass
class _Bucket:
    tokens: int
    last_replenished: float


class TokenBucketQuotaAllocator:
    """Bugged implementation where added == 0 still overwrites last_replenished."""

    def __init__(
        self,
        capacity: int,
        refill_rate_per_sec: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if capacity < 1 or refill_rate_per_sec <= 0:
            raise ValueError("capacity >= 1 and refill_rate_per_sec > 0 required")
        self._capacity = capacity
        self._refill_rate_per_sec = refill_rate_per_sec
        self._clock = clock
        self._lock = threading.RLock()
        self._buckets: dict[str, _Bucket] = {}

    def _get_or_create(self, key: str, now: float) -> _Bucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(tokens=self._capacity, last_replenished=now)
            self._buckets[key] = bucket
        return bucket

    def _replenish(self, bucket: _Bucket, now: float) -> None:
        elapsed = max(0.0, now - bucket.last_replenished)
        added = int(elapsed * self._refill_rate_per_sec)
        bucket.tokens = min(self._capacity, bucket.tokens + added)
        # DRIFT BUG (Violates REQ-0005): unconditionally overwrites last_replenished!
        bucket.last_replenished = now

    def consume(self, key: str, amount: int = 1) -> bool:
        if not key or amount < 1:
            raise ValueError("key must be non-empty and amount >= 1")
        with self._lock:
            now = self._clock()
            bucket = self._get_or_create(key, now)
            self._replenish(bucket, now)
            if bucket.tokens < amount:
                return False
            bucket.tokens -= amount
            return True

    def available_tokens(self, key: str) -> int:
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            now = self._clock()
            bucket = self._get_or_create(key, now)
            self._replenish(bucket, now)
            return bucket.tokens
