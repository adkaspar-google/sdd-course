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
"""OrderPulse workflow engine implemented across Sprints 1-3 (Standalone Superpowers)."""

from typing import Any, Dict, List, Optional


class RateLimitExceededError(ValueError):
    """Raised when a customer exceeds the sliding-window order rate limit."""


class DownstreamServiceError(RuntimeError):
    """Raised when a downstream SaaS service (Billing or Slack) fails."""


PRIORITY_RANK: Dict[str, int] = {
    "HIGH": 0,
    "MEDIUM": 1,
    "LOW": 2,
}


class OrderPulseEngine:
    """Coordinates OrdersDB, Billing, InventoryLedger, and SlackNotifier."""

    def __init__(self, initial_stock: Optional[Dict[str, int]] = None) -> None:
        self.stock: Dict[str, int] = dict(initial_stock or {})
        self.orders: List[Dict[str, Any]] = []
        self.charges: List[Dict[str, Any]] = []
        self.slack_messages: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []

    def process_order(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an incoming order event across Inventory, Billing, and Slack."""
        event_id = event["event_id"]
        for existing in self.orders:
            if existing["event_id"] == event_id:
                return dict(existing)

        sku = event["sku"]
        qty = event["qty"]
        if qty <= 0:
            raise ValueError("qty must be positive")

        customer_id = event["customer_id"]
        timestamp = event.get("timestamp", 0)
        recent_customer_orders = [
            o
            for o in self.orders
            if o["customer_id"] == customer_id
            and 0 <= timestamp - o.get("timestamp", 0) <= 60
        ]
        if len(recent_customer_orders) >= 3:
            raise RateLimitExceededError(
                f"Customer {customer_id} exceeded 3 orders per 60s window"
            )

        if self.stock.get(sku, 0) < qty:
            raise ValueError("insufficient stock")

        stock_snapshot = dict(self.stock)
        charges_len = len(self.charges)
        slack_len = len(self.slack_messages)
        orders_len = len(self.orders)

        try:
            self.stock[sku] -= qty
            if event.get("simulate_billing_failure"):
                raise DownstreamServiceError("Billing gateway declined")

            total_cents = event["total_cents"]
            charge = {
                "event_id": event_id,
                "customer_id": customer_id,
                "amount_cents": total_cents,
            }
            self.charges.append(charge)

            if event.get("simulate_slack_failure"):
                raise DownstreamServiceError("Slack webhook timeout")

            is_vip = total_cents >= 100000
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
                "total_cents": total_cents,
                "priority": priority,
                "timestamp": timestamp,
                "channel": channel,
                "status": "CONFIRMED",
            }
            self.orders.append(record)
            self.audit_log.append({"event_id": event_id, "status": "CONFIRMED"})
            return dict(record)
        except DownstreamServiceError:
            self.stock = stock_snapshot
            del self.charges[charges_len:]
            del self.slack_messages[slack_len:]
            del self.orders[orders_len:]
            raise

    def list_pending_fulfillments(self) -> List[Dict[str, Any]]:
        """Returns confirmed orders sorted by priority (HIGH -> MEDIUM -> LOW)."""
        return sorted(
            (dict(o) for o in self.orders),
            key=lambda o: PRIORITY_RANK.get(o.get("priority", "MEDIUM"), 1),
        )
