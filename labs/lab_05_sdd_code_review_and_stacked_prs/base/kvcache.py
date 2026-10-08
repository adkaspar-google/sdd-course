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

"""Baseline bounded FIFO Key-Value Cache (REQ-0001..REQ-0005)."""

from __future__ import annotations

from collections import OrderedDict
import threading
from typing import Any, Optional


class KVCache:
    """Thread-safe bounded key-value cache with strict FIFO eviction."""

    def __init__(self, max_size: int = 128) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._lock = threading.RLock()
        self._store: OrderedDict[str, Any] = OrderedDict()

    def put(self, key: str, value: Any) -> None:
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            if key in self._store:
                self._store[key] = value
                return
            if len(self._store) >= self._max_size:
                self._store.popitem(last=False)
            self._store[key] = value

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            return self._store.get(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
