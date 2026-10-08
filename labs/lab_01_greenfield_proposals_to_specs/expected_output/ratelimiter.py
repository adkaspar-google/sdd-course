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

"""Reference Sliding-Window Rate Limiter implementing REQ-0001..REQ-0006."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time
from typing import Callable


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: float


class SlidingWindowRateLimiter:
    """Thread-safe per-key sliding-window rate limiter with cost and retry_after."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._limit = limit
        self._window_seconds = window_seconds
        self._clock = clock
        self._lock = threading.RLock()
        self._logs: dict[str, deque[tuple[float, int]]] = {}

    def _evict_expired(
        self, log: deque[tuple[float, int]], now: float
    ) -> int:
        cutoff = now - self._window_seconds
        while log and log[0][0] <= cutoff:
            log.popleft()
        return sum(cost for _, cost in log)

    def allow(self, key: str, cost: int = 1) -> RateLimitDecision:
        if not key:
            raise ValueError("key must be non-empty")
        if cost < 1 or cost > self._limit:
            raise ValueError("cost must be between 1 and limit")

        with self._lock:
            now = self._clock()
            log = self._logs.setdefault(key, deque())
            used = self._evict_expired(log, now)

            if used + cost <= self._limit:
                log.append((now, cost))
                return RateLimitDecision(
                    allowed=True,
                    remaining=self._limit - (used + cost),
                    retry_after_seconds=0.0,
                )

            needed_to_free = (used + cost) - self._limit
            freed = 0
            retry_after = 0.0
            for ts, entry_cost in log:
                freed += entry_cost
                if freed >= needed_to_free:
                    retry_after = max(0.0, (ts + self._window_seconds) - now)
                    break

            return RateLimitDecision(
                allowed=False,
                remaining=max(0, self._limit - used),
                retry_after_seconds=round(retry_after, 6),
            )

    def reset(self, key: str) -> None:
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._logs.pop(key, None)
