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
"""OrderPulse workflow engine (Vibe-coded implementation)."""

import csv
import io
from typing import Any, Dict, List, Optional


class RateLimitExceededError(ValueError):
    """Raised when a customer exceeds the sliding-window order rate limit."""


class DownstreamServiceError(RuntimeError):
    """Raised when a downstream SaaS service (Billing or Slack) fails."""


PRIORITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


class OrderPulseEngine:
    """Coordinates OrdersDB, Billing, InventoryLedger, and SlackNotifier."""

    def __init__(self, initial_stock: Optional[Dict[str, int]] = None) -> None:
        self.stock: Dict[str, int] = dict(initial_stock or {})
        self.orders: List[Dict[str, Any]] = []
        self.charges: List[Dict[str, Any]] = []
        self.slack_messages: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []
        self._orders_by_id: Dict[str, Dict[str, Any]] = {}

    def apply_promo_discount(self, total_cents: int, discount_pct: float) -> int:
        """Applies a promotional percentage discount to an order total."""
        if discount_pct <= 0:
            return total_cents
        return max(0, int(round(total_cents * (1.0 - discount_pct / 100.0))))

    def export_csv(self) -> str:
        """Exports confirmed orders as a CSV string."""
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=[
                "event_id",
                "customer_id",
                "sku",
                "qty",
                "total_cents",
                "priority",
                "timestamp",
                "channel",
                "status",
            ],
        )
        writer.writeheader()
        for order in self.orders:
            writer.writerow(order)
        return buf.getvalue()

    def process_order(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an incoming order event across Inventory, Billing, and Slack."""
        event_id = event["event_id"]
        if event_id in self._orders_by_id:
            return dict(self._orders_by_id[event_id])

        sku = event["sku"]
        qty = event["qty"]
        if qty <= 0:
            raise ValueError("qty must be positive")
        if self.stock.get(sku, 0) < qty:
            raise ValueError("insufficient stock")

        customer_id = event["customer_id"]
        now = event.get("timestamp", 0)
        recent = [
            o
            for o in self.orders
            if o["customer_id"] == customer_id and (now - o["timestamp"]) < 60
        ]
        if len(recent) >= 3:
            raise RateLimitExceededError("Rate limit of 3 orders per 60s exceeded")

        self.stock[sku] -= qty
        if event.get("simulate_billing_failure"):
            self.stock[sku] += qty
            self.audit_log.append({"event_id": event_id, "status": "ROLLED_BACK"})
            raise DownstreamServiceError("Billing gateway declined")

        charge = {
            "event_id": event_id,
            "customer_id": customer_id,
            "amount_cents": event["total_cents"],
        }
        self.charges.append(charge)

        if event.get("simulate_slack_failure"):
            self.charges.pop()
            self.stock[sku] += qty
            self.audit_log.append({"event_id": event_id, "status": "ROLLED_BACK"})
            raise DownstreamServiceError("Slack webhook timeout")

        is_vip = event["total_cents"] > 100000
        channel = "#vip-orders" if is_vip else "#orders"
        priority = "HIGH" if is_vip else event.get("priority", "MEDIUM")

        self.slack_messages.append(
            {
                "event_id": event_id,
                "channel": channel,
                "priority": priority,
            }
        )
        record = {
            "event_id": event_id,
            "customer_id": customer_id,
            "sku": sku,
            "qty": qty,
            "total_cents": event["total_cents"],
            "priority": priority,
            "timestamp": now,
            "channel": channel,
            "status": "CONFIRMED",
        }
        self.orders.append(record)
        self._orders_by_id[event_id] = record
        self.audit_log.append({"event_id": event_id, "status": "CONFIRMED"})
        return dict(record)

    def list_pending_fulfillments(self) -> List[Dict[str, Any]]:
        """Returns confirmed orders sorted by priority."""
        return sorted(
            [dict(o) for o in self.orders],
            key=lambda o: PRIORITY_RANK.get(o["priority"], 99),
        )
