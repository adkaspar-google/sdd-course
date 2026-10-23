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
"""Starter module for IL-T1: SubscriptionWebhookEngine."""

import copy
from typing import Any, Dict, List


VALID_EVENT_TYPES = frozenset({
    "SUBSCRIPTION_CREATED",
    "PLAN_UPGRADED",
    "SUBSCRIPTION_CANCELED",
})


class SubscriptionWebhookEngine:
    """Processes subscription billing webhooks across state stores."""

    def __init__(self) -> None:
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.invoices: List[Dict[str, Any]] = []
        self.entitlements: Dict[str, Dict[str, Any]] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        self._processed_results: Dict[str, Dict[str, Any]] = {}
        self._tenant_timestamps: Dict[str, List[int]] = {}
        self._creation_order: Dict[str, int] = {}
        self._next_creation_seq: int = 0

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a webhook payload with idempotency, rate limiting, and rollback."""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dict")

        webhook_id = payload.get("webhook_id")
        if not isinstance(webhook_id, str) or not webhook_id.strip():
            raise ValueError("webhook_id must be a non-empty string")

        # 1. Replay-safe idempotency check prior to validation/rate-limiting side effects
        if webhook_id in self._processed_results:
            return copy.deepcopy(self._processed_results[webhook_id])

        tenant_id = payload.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

        event_type = payload.get("event_type")
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Unsupported event_type: {event_type}")

        seats = payload.get("seats")
        if (
            seats is None
            or isinstance(seats, bool)
            or not isinstance(seats, int)
        ):
            raise ValueError("seats must be an integer")

        amount_cents = payload.get("amount_cents")
        if (
            amount_cents is None
            or isinstance(amount_cents, bool)
            or not isinstance(amount_cents, int)
        ):
            raise ValueError("amount_cents must be an integer")

        if amount_cents < 0:
            raise ValueError("amount_cents cannot be negative")

        if event_type in ("SUBSCRIPTION_CREATED", "PLAN_UPGRADED"):
            if seats <= 0:
                raise ValueError("seats must be positive for creation or upgrade")
        else:
            if seats < 0:
                raise ValueError("seats cannot be negative")

        existing_sub = self.subscriptions.get(tenant_id)
        has_active_sub = (
            existing_sub is not None and existing_sub.get("status") == "ACTIVE"
        )
        if event_type in ("PLAN_UPGRADED", "SUBSCRIPTION_CANCELED") and not has_active_sub:
            raise ValueError(
                f"Cannot execute {event_type} for tenant {tenant_id} without an active subscription"
            )

        timestamp = payload.get("timestamp", 0)
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            raise ValueError("timestamp must be numeric")

        # 2. Sliding-window rate limit: max 4 successful webhooks in [timestamp - 60, timestamp]
        prior_timestamps = self._tenant_timestamps.get(tenant_id, [])
        recent_count = sum(
            1 for prev_ts in prior_timestamps if 0 <= timestamp - prev_ts <= 60
        )
        if recent_count >= 4:
            raise ValueError("Rate limit exceeded")

        # 3. Determine tier and SLA
        tier = "ENTERPRISE" if (seats >= 50 or amount_cents >= 500000) else "STANDARD"
        sla_hours = 1 if tier == "ENTERPRISE" else 24

        record = {
            "webhook_id": webhook_id,
            "tenant_id": tenant_id,
            "plan": payload.get("plan"),
            "seats": seats,
            "amount_cents": amount_cents,
            "tier": tier,
            "sla_hours": sla_hours,
            "status": "ACTIVE" if event_type != "SUBSCRIPTION_CANCELED" else "CANCELED",
            "timestamp": timestamp,
        }

        # 4. Transactional execution with rollback on entitlement sync failure
        subs_snapshot = copy.deepcopy(self.subscriptions)
        invoices_snapshot = copy.deepcopy(self.invoices)
        entitlements_snapshot = copy.deepcopy(self.entitlements)
        creation_order_snapshot = dict(self._creation_order)
        next_seq_snapshot = self._next_creation_seq

        try:
            if event_type == "SUBSCRIPTION_CREATED" or tenant_id not in self._creation_order:
                self._creation_order[tenant_id] = self._next_creation_seq
                self._next_creation_seq += 1

            self.subscriptions[tenant_id] = record
            self.invoices.append({"webhook_id": webhook_id, "amount_cents": amount_cents})

            if payload.get("fail_entitlement_sync"):
                raise RuntimeError("Entitlement service unavailable")

            self.entitlements[tenant_id] = {"seats": seats, "tier": tier}
        except RuntimeError:
            self.subscriptions = subs_snapshot
            self.invoices = invoices_snapshot
            self.entitlements = entitlements_snapshot
            self._creation_order = creation_order_snapshot
            self._next_creation_seq = next_seq_snapshot
            self.audit_trail.append({"webhook_id": webhook_id, "status": "ROLLED_BACK"})
            raise

        self.audit_trail.append({"webhook_id": webhook_id, "status": "PROCESSED"})
        self._tenant_timestamps.setdefault(tenant_id, []).append(timestamp)
        self._processed_results[webhook_id] = copy.deepcopy(record)
        return copy.deepcopy(record)

    def list_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Returns active subscriptions ordered by ENTERPRISE before STANDARD, then creation order."""
        active = [
            copy.deepcopy(sub)
            for sub in self.subscriptions.values()
            if sub.get("status") == "ACTIVE"
        ]
        active.sort(
            key=lambda sub: (
                0 if sub.get("tier") == "ENTERPRISE" else 1,
                self._creation_order.get(sub.get("tenant_id", ""), 0),
            )
        )
        return active
