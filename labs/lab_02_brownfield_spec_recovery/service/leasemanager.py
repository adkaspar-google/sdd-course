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

"""Brownfield Distributed Lease Lock Manager with monotonic fencing tokens."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Callable, Optional


@dataclass(frozen=True)
class Lease:
    resource_id: str
    holder_id: str
    fencing_token: int
    expires_at: float


class LeaseManager:
    """Thread-safe lease lock manager issuing monotonic 64-bit fencing tokens."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.RLock()
        self._next_token: int = 1
        self._leases: dict[str, Lease] = {}

    def _issue_token(self) -> int:
        token = self._next_token
        self._next_token += 1
        return token

    def _purge_if_expired(self, resource_id: str, now: float) -> None:
        current = self._leases.get(resource_id)
        if current is not None and current.expires_at <= now:
            del self._leases[resource_id]

    def acquire(
        self, resource_id: str, holder_id: str, ttl_seconds: float
    ) -> Optional[Lease]:
        if not resource_id or not holder_id:
            raise ValueError("resource_id and holder_id must be non-empty")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")

        with self._lock:
            now = self._clock()
            self._purge_if_expired(resource_id, now)
            existing = self._leases.get(resource_id)
            if existing is not None and existing.holder_id != holder_id:
                return None
            lease = Lease(
                resource_id=resource_id,
                holder_id=holder_id,
                fencing_token=self._issue_token(),
                expires_at=now + ttl_seconds,
            )
            self._leases[resource_id] = lease
            return lease

    def renew(
        self,
        resource_id: str,
        holder_id: str,
        fencing_token: int,
        ttl_seconds: float,
    ) -> Optional[Lease]:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        with self._lock:
            now = self._clock()
            self._purge_if_expired(resource_id, now)
            existing = self._leases.get(resource_id)
            if (
                existing is None
                or existing.holder_id != holder_id
                or existing.fencing_token != fencing_token
            ):
                return None
            renewed = Lease(
                resource_id=resource_id,
                holder_id=holder_id,
                fencing_token=self._issue_token(),
                expires_at=now + ttl_seconds,
            )
            self._leases[resource_id] = renewed
            return renewed

    def release(
        self, resource_id: str, holder_id: str, fencing_token: int
    ) -> bool:
        with self._lock:
            now = self._clock()
            self._purge_if_expired(resource_id, now)
            existing = self._leases.get(resource_id)
            if (
                existing is None
                or existing.holder_id != holder_id
                or existing.fencing_token != fencing_token
            ):
                return False
            del self._leases[resource_id]
            return True

    def get_lease(self, resource_id: str) -> Optional[Lease]:
        with self._lock:
            now = self._clock()
            self._purge_if_expired(resource_id, now)
            return self._leases.get(resource_id)

    def evict_expired(self) -> int:
        with self._lock:
            now = self._clock()
            expired_keys = [
                k for k, v in self._leases.items() if v.expires_at <= now
            ]
            for k in expired_keys:
                del self._leases[k]
            return len(expired_keys)
