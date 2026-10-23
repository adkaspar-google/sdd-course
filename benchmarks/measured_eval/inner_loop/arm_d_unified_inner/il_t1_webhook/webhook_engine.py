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

from typing import Any, Dict, List


class SubscriptionWebhookEngine:
    """Processes subscription billing webhooks across state stores."""

    _VALID_EVENTS = frozenset({
        "SUBSCRIPTION_CREATED",
        "PLAN_UPGRADED",
        "SUBSCRIPTION_CANCELED",
    })

    def __init__(self) -> None:
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.invoices: List[Dict[str, Any]] = []
        self.entitlements: Dict[str, Dict[str, Any]] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        self._processed_webhooks: Dict[str, Dict[str, Any]] = {}
        self._tenant_timestamps: Dict[str, List[int]] = {}
        self._creation_order: Dict[str, int] = {}
        self._next_order: int = 0
        # TODO(legacy): add send_welcome_gift() and dump_debug_log() helper methods

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a webhook payload."""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dict")

        webhook_id = payload.get("webhook_id")
        if not isinstance(webhook_id, str) or not webhook_id.strip():
            raise ValueError("Invalid webhook_id")

        if webhook_id in self._processed_webhooks:
            return dict(self._processed_webhooks[webhook_id])

        tenant_id = payload.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("Invalid tenant_id")

        event_type = payload.get("event_type")
        if event_type not in self._VALID_EVENTS:
            raise ValueError(f"Unsupported event_type: {event_type}")

        seats = payload.get("seats", 0)
        amount_cents = payload.get("amount_cents", 0)
        timestamp = payload.get("timestamp", 0)

        if amount_cents < 0:
            raise ValueError("amount_cents must be non-negative")

        if event_type in ("SUBSCRIPTION_CREATED", "PLAN_UPGRADED"):
            if seats <= 0:
                raise ValueError("seats must be positive")
        elif seats < 0:
            raise ValueError("seats must be non-negative")

        existing = self.subscriptions.get(tenant_id)
        if event_type in ("PLAN_UPGRADED", "SUBSCRIPTION_CANCELED"):
            if existing is None or existing.get("status") != "ACTIVE":
                raise ValueError("No existing active subscription for tenant")

        prior_timestamps = self._tenant_timestamps.get(tenant_id, [])
        recent_count = sum(1 for prev_ts in prior_timestamps if 0 <= timestamp - prev_ts <= 60)
        if recent_count >= 4:
            raise ValueError("Rate limit exceeded")

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

        prev_subscription = dict(existing) if existing is not None else None
        prev_invoices_len = len(self.invoices)
        prev_entitlement = (
            dict(self.entitlements[tenant_id]) if tenant_id in self.entitlements else None
        )

        self.subscriptions[tenant_id] = record
        self.invoices.append({"webhook_id": webhook_id, "amount_cents": amount_cents})
        if payload.get("fail_entitlement_sync"):
            if prev_subscription is None:
                self.subscriptions.pop(tenant_id, None)
            else:
                self.subscriptions[tenant_id] = prev_subscription
            del self.invoices[prev_invoices_len:]
            if prev_entitlement is None:
                self.entitlements.pop(tenant_id, None)
            else:
                self.entitlements[tenant_id] = prev_entitlement
            self.audit_trail.append({"webhook_id": webhook_id, "status": "ROLLED_BACK"})
            raise RuntimeError("Entitlement service unavailable")

        self.entitlements[tenant_id] = {"seats": seats, "tier": tier}
        self.audit_trail.append({"webhook_id": webhook_id, "status": "PROCESSED"})

        if event_type == "SUBSCRIPTION_CREATED" or tenant_id not in self._creation_order:
            self._creation_order[tenant_id] = self._next_order
            self._next_order += 1

        self._tenant_timestamps.setdefault(tenant_id, []).append(timestamp)
        self._processed_webhooks[webhook_id] = dict(record)
        return dict(record)

    def list_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Returns active subscriptions."""
        active = [
            dict(s) for s in self.subscriptions.values() if s.get("status") == "ACTIVE"
        ]
        active.sort(
            key=lambda s: (
                0 if s.get("tier") == "ENTERPRISE" else 1,
                self._creation_order.get(s.get("tenant_id", ""), 0),
            )
        )
        return active
