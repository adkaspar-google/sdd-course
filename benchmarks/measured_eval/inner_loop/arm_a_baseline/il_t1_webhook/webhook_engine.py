"""Starter module for IL-T1: SubscriptionWebhookEngine."""

import copy
from typing import Any, Dict, List


class SubscriptionWebhookEngine:
    """Processes subscription billing webhooks across state stores."""

    SUPPORTED_EVENTS = frozenset({
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
        self._tenant_timestamps: Dict[str, List[float | int]] = {}
        self._creation_order: Dict[str, int] = {}
        self._creation_seq: int = 0
        # TODO(legacy): add send_welcome_gift() and dump_debug_log() helper methods

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a webhook payload."""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dict")

        webhook_id = payload.get("webhook_id")
        if not isinstance(webhook_id, str) or not webhook_id.strip():
            raise ValueError("webhook_id must be a non-blank string")

        if webhook_id in self._processed_webhooks:
            return copy.deepcopy(self._processed_webhooks[webhook_id])

        tenant_id = payload.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id must be a non-blank string")

        event_type = payload.get("event_type")
        if event_type not in self.SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported event_type: {event_type}")

        seats = payload.get("seats", 0)
        amount_cents = payload.get("amount_cents", 0)
        timestamp = payload.get("timestamp", 0)

        if (
            isinstance(amount_cents, bool)
            or not isinstance(amount_cents, (int, float))
            or amount_cents < 0
        ):
            raise ValueError("amount_cents must be non-negative")

        if isinstance(seats, bool) or not isinstance(seats, int):
            raise ValueError("seats must be an integer")

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
                f"Tenant '{tenant_id}' does not have an existing active subscription"
            )

        tenant_history = self._tenant_timestamps.get(tenant_id, [])
        recent_count = sum(
            1 for prev_ts in tenant_history if 0 <= timestamp - prev_ts <= 60
        )
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

        prev_subscriptions = copy.deepcopy(self.subscriptions)
        prev_invoices = copy.deepcopy(self.invoices)
        prev_entitlements = copy.deepcopy(self.entitlements)
        prev_creation_order = copy.deepcopy(self._creation_order)
        prev_creation_seq = self._creation_seq

        if tenant_id not in self._creation_order:
            self._creation_seq += 1
            self._creation_order[tenant_id] = self._creation_seq

        self.subscriptions[tenant_id] = record
        self.invoices.append({"webhook_id": webhook_id, "amount_cents": amount_cents})
        if payload.get("fail_entitlement_sync"):
            self.subscriptions.clear()
            self.subscriptions.update(prev_subscriptions)
            self.invoices[:] = prev_invoices
            self.entitlements.clear()
            self.entitlements.update(prev_entitlements)
            self._creation_order.clear()
            self._creation_order.update(prev_creation_order)
            self._creation_seq = prev_creation_seq
            self.audit_trail.append({"webhook_id": webhook_id, "status": "ROLLED_BACK"})
            raise RuntimeError("Entitlement service unavailable")

        self.entitlements[tenant_id] = {"seats": seats, "tier": tier}
        self.audit_trail.append({"webhook_id": webhook_id, "status": "PROCESSED"})
        self._tenant_timestamps.setdefault(tenant_id, []).append(timestamp)
        self._processed_webhooks[webhook_id] = copy.deepcopy(record)
        return copy.deepcopy(record)

    def list_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Returns active subscriptions."""
        active = [
            s for s in self.subscriptions.values() if s.get("status") == "ACTIVE"
        ]
        active.sort(
            key=lambda s: (
                0 if s.get("tier") == "ENTERPRISE" else 1,
                self._creation_order.get(s.get("tenant_id", ""), 0),
            )
        )
        return [copy.deepcopy(s) for s in active]
