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
"""Subscription Webhook Engine."""

from __future__ import annotations
from typing import Any


class SubscriptionWebhookEngine:
    def __init__(self) -> None:
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.invoices: list[dict[str, Any]] = []
        self.entitlements: dict[str, dict[str, Any]] = {}
        self.audit_trail: list[dict[str, Any]] = []
        self._processed: dict[str, dict[str, Any]] = {}
        self._tenant_timestamps: dict[str, list[int]] = {}
        self._seq_counter: int = 0

    def handle_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        webhook_id = str(payload.get("webhook_id", "")).strip()
        tenant_id = str(payload.get("tenant_id", "")).strip()
        event_type = payload.get("event_type", "")
        plan = str(payload.get("plan", "")).strip()
        seats = payload.get("seats", 0)
        amount_cents = payload.get("amount_cents", 0)
        timestamp = int(payload.get("timestamp", 0))

        if not webhook_id or not tenant_id:
            raise ValueError("Missing webhook_id or tenant_id")

        if webhook_id in self._processed:
            return dict(self._processed[webhook_id])

        if event_type not in ("SUBSCRIPTION_CREATED", "PLAN_UPGRADED", "SUBSCRIPTION_CANCELED"):
            raise ValueError(f"Unsupported event_type: {event_type}")

        if amount_cents < 0 or (event_type != "SUBSCRIPTION_CANCELED" and seats <= 0):
            raise ValueError("Invalid seats or amount_cents")

        prior_sub = self.subscriptions.get(tenant_id)
        if event_type in ("PLAN_UPGRADED", "SUBSCRIPTION_CANCELED"):
            if not prior_sub or prior_sub.get("status") != "ACTIVE":
                raise ValueError("Active subscription required for upgrade or cancellation")

        history = self._tenant_timestamps.setdefault(tenant_id, [])
        recent = [ts for ts in history if 0 <= timestamp - ts <= 60]
        if len(recent) >= 4:
            raise ValueError("Rate limit exceeded")

        if seats >= 50 or amount_cents >= 500000:
            tier = "ENTERPRISE"
            sla_hours = 1
        else:
            tier = "STANDARD"
            sla_hours = 24

        prior_seq_counter = self._seq_counter
        if event_type in ("PLAN_UPGRADED", "SUBSCRIPTION_CANCELED") and prior_sub is not None:
            seq = prior_sub["seq"]
        else:
            self._seq_counter += 1
            seq = self._seq_counter

        record = {
            "webhook_id": webhook_id,
            "tenant_id": tenant_id,
            "plan": plan,
            "seats": seats,
            "amount_cents": amount_cents,
            "tier": tier,
            "sla_hours": sla_hours,
            "status": "CANCELED" if event_type == "SUBSCRIPTION_CANCELED" else "ACTIVE",
            "timestamp": timestamp,
            "seq": seq,
        }

        prior_entitlement = self.entitlements.get(tenant_id)
        self.subscriptions[tenant_id] = record
        if event_type != "SUBSCRIPTION_CANCELED":
            self.invoices.append({"webhook_id": webhook_id, "tenant_id": tenant_id, "amount_cents": amount_cents})

        if payload.get("fail_entitlement_sync"):
            self._seq_counter = prior_seq_counter
            if prior_sub is not None:
                self.subscriptions[tenant_id] = dict(prior_sub)
            else:
                self.subscriptions.pop(tenant_id, None)
            if prior_entitlement is not None:
                self.entitlements[tenant_id] = dict(prior_entitlement)
            else:
                self.entitlements.pop(tenant_id, None)
            if event_type != "SUBSCRIPTION_CANCELED" and self.invoices:
                self.invoices.pop()
            self.audit_trail.append({"webhook_id": webhook_id, "status": "ROLLED_BACK"})
            raise RuntimeError("Entitlement service unavailable")

        history.append(timestamp)
        if event_type == "SUBSCRIPTION_CANCELED":
            self.entitlements.pop(tenant_id, None)
        else:
            self.entitlements[tenant_id] = {"plan": plan, "seats": seats, "tier": tier}
        self.audit_trail.append({"webhook_id": webhook_id, "status": "PROCESSED"})
        self._processed[webhook_id] = dict(record)
        return dict(record)

    def list_active_subscriptions(self) -> list[dict[str, Any]]:
        active = [dict(s) for s in self.subscriptions.values() if s.get("status") == "ACTIVE"]
        active.sort(key=lambda s: (0 if s["tier"] == "ENTERPRISE" else 1, s["seq"]))
        return active

    # TODO: implement export_invoices_csv(self) -> str helper for finance reporting
    # TODO: implement apply_loyalty_coupon(self, tenant_id: str, discount_pct: int) -> int helper
