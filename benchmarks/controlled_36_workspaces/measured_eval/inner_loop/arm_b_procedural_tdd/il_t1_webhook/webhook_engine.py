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
"""Production module for IL-T1: SubscriptionWebhookEngine."""

import copy
from typing import Any, Dict, List


SUPPORTED_EVENTS = frozenset({
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
        self._processed_webhooks: Dict[str, Dict[str, Any]] = {}
        self._tenant_timestamps: Dict[str, List[int]] = {}
        self._creation_order: Dict[str, int] = {}
        self._creation_seq: int = 0

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a webhook payload with validation, idempotency, rate limiting, and rollback."""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")

        webhook_id = payload.get("webhook_id")
        if isinstance(webhook_id, str) and webhook_id in self._processed_webhooks:
            return dict(self._processed_webhooks[webhook_id])

        if not isinstance(webhook_id, str) or not webhook_id.strip():
            raise ValueError("webhook_id must be a non-empty string")

        tenant_id = payload.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-empty string")

        event_type = payload.get("event_type")
        if event_type not in SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported event_type: {event_type}")

        seats = payload.get("seats")
        amount_cents = payload.get("amount_cents")
        if (
            seats is None
            or isinstance(seats, bool)
            or not isinstance(seats, (int, float))
        ):
            raise ValueError("seats must be a number")
        if (
            amount_cents is None
            or isinstance(amount_cents, bool)
            or not isinstance(amount_cents, (int, float))
        ):
            raise ValueError("amount_cents must be a number")

        if amount_cents < 0:
            raise ValueError("amount_cents cannot be negative")

        if event_type in ("SUBSCRIPTION_CREATED", "PLAN_UPGRADED"):
            if seats <= 0:
                raise ValueError("seats must be positive")
        else:
            if seats < 0:
                raise ValueError("seats cannot be negative")

        existing_sub = self.subscriptions.get(tenant_id)
        if event_type in ("PLAN_UPGRADED", "SUBSCRIPTION_CANCELED"):
            if existing_sub is None or existing_sub.get("status") != "ACTIVE":
                raise ValueError("Tenant does not have an active subscription")

        timestamp = payload.get("timestamp", 0)
        if timestamp is None or isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            raise ValueError("timestamp must be numeric")

        recent_timestamps = self._tenant_timestamps.get(tenant_id, [])
        in_window_count = sum(
            1 for prev_ts in recent_timestamps if 0 <= (timestamp - prev_ts) <= 60
        )
        if in_window_count >= 4:
            raise ValueError("Rate limit exceeded")

        snap_subscriptions = copy.deepcopy(self.subscriptions)
        snap_invoices = copy.deepcopy(self.invoices)
        snap_entitlements = copy.deepcopy(self.entitlements)
        snap_creation_order = copy.deepcopy(self._creation_order)
        snap_creation_seq = self._creation_seq

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

        try:
            self.subscriptions[tenant_id] = record
            if event_type == "SUBSCRIPTION_CREATED":
                self._creation_seq += 1
                self._creation_order[tenant_id] = self._creation_seq

            self.invoices.append({"webhook_id": webhook_id, "amount_cents": amount_cents})
            if payload.get("fail_entitlement_sync"):
                raise RuntimeError("Entitlement service unavailable")

            self.entitlements[tenant_id] = {"seats": seats, "tier": tier}
        except RuntimeError:
            self.subscriptions = snap_subscriptions
            self.invoices = snap_invoices
            self.entitlements = snap_entitlements
            self._creation_order = snap_creation_order
            self._creation_seq = snap_creation_seq
            self.audit_trail.append({"webhook_id": webhook_id, "status": "ROLLED_BACK"})
            raise

        self.audit_trail.append({"webhook_id": webhook_id, "status": "PROCESSED"})
        self._tenant_timestamps.setdefault(tenant_id, []).append(timestamp)
        self._processed_webhooks[webhook_id] = dict(record)
        return dict(record)

    def list_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Returns active subscriptions ordered by ENTERPRISE before STANDARD, then creation order."""
        active = [
            dict(s)
            for s in self.subscriptions.values()
            if s.get("status") == "ACTIVE"
        ]
        active.sort(
            key=lambda s: (
                0 if s.get("tier") == "ENTERPRISE" else 1,
                self._creation_order.get(s.get("tenant_id", ""), 0),
            )
        )
        return active
