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

"""Circuit Breaker state machine implementing REQ-0001 through REQ-0007."""

from __future__ import annotations

from enum import Enum
import threading
import time
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(RuntimeError):
    """Raised when a call is rejected because the circuit is OPEN."""


class CircuitBreaker:
    """Thread-safe Circuit Breaker with CLOSED -> OPEN -> HALF_OPEN recovery."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout_seconds <= 0:
            raise ValueError("recovery_timeout_seconds must be > 0")
        self._failure_threshold = failure_threshold
        self._recovery_timeout_seconds = recovery_timeout_seconds
        self._clock = clock
        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: Optional[float] = None

    def _refresh_state(self, now: float) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (now - self._opened_at) >= self._recovery_timeout_seconds
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._refresh_state(self._clock())

    @property
    def consecutive_failures(self) -> int:
        with self._lock:
            return self._consecutive_failures

    def call(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        with self._lock:
            now = self._clock()
            current_state = self._refresh_state(now)
            if current_state == CircuitState.OPEN:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = fn(*args, **kwargs)
        except Exception:
            with self._lock:
                now_fail = self._clock()
                self._consecutive_failures += 1
                if (
                    current_state == CircuitState.HALF_OPEN
                    or self._consecutive_failures >= self._failure_threshold
                ):
                    self._state = CircuitState.OPEN
                    self._opened_at = now_fail
            raise

        with self._lock:
            self._consecutive_failures = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None
            return result
