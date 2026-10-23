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
"""QuotaEnforcer implementation with 1-window 50% carryover and burst cap."""

from __future__ import annotations
from typing import Any


class QuotaEnforcer:
    def __init__(self) -> None:
        self.tenants: dict[str, dict[str, Any]] = {}

    def configure_tenant(self, tenant_id: str, base_limit: int, burst_cap: int) -> None:
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("Invalid tenant_id")
        if isinstance(base_limit, bool) or not isinstance(base_limit, int) or base_limit <= 0:
            raise ValueError("Invalid base_limit")
        if isinstance(burst_cap, bool) or not isinstance(burst_cap, int) or burst_cap < 0:
            raise ValueError("Invalid burst_cap")
        tid = tenant_id.strip()
        self.tenants[tid] = {
            "tenant_id": tid,
            "base_limit": base_limit,
            "burst_cap": burst_cap,
            "current_window": None,
            "consumed_in_window": 0,
            "carryover": 0,
        }

    def _advance_window(self, state: dict[str, Any], window_idx: int) -> None:
        cur = state["current_window"]
        if cur is None:
            state["current_window"] = window_idx
            state["consumed_in_window"] = 0
            state["carryover"] = 0
            return
        if window_idx < cur:
            raise ValueError("Out-of-order window_idx")
        if window_idx == cur:
            return
        if window_idx == cur + 1:
            unused = max(0, state["base_limit"] - state["consumed_in_window"])
            state["carryover"] = min(state["burst_cap"], unused // 2)
        else:
            state["carryover"] = 0
        state["current_window"] = window_idx
        state["consumed_in_window"] = 0

    def consume(self, tenant_id: str, units: int, window_idx: int) -> dict[str, Any]:
        if not isinstance(tenant_id, str) or tenant_id.strip() not in self.tenants:
            raise ValueError("Unknown tenant")
        if isinstance(units, bool) or not isinstance(units, int) or units <= 0:
            raise ValueError("Invalid units")
        if isinstance(window_idx, bool) or not isinstance(window_idx, int) or window_idx < 0:
            raise ValueError("Invalid window_idx")

        state = self.tenants[tenant_id.strip()]
        self._advance_window(state, window_idx)
        effective_limit = state["base_limit"] + state["carryover"]
        if state["consumed_in_window"] + units > effective_limit:
            return {
                "allowed": False,
                "effective_limit": effective_limit,
                "remaining": effective_limit - state["consumed_in_window"],
                "carryover": state["carryover"],
            }
        state["consumed_in_window"] += units
        return {
            "allowed": True,
            "effective_limit": effective_limit,
            "remaining": effective_limit - state["consumed_in_window"],
            "carryover": state["carryover"],
        }
