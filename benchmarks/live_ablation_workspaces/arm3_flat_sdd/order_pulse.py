"""OrderPulse workflow engine implemented under Flat Outer-Loop SDD (OpenSpec + Conductor)."""

from typing import Any, Dict, List, Optional


class RateLimitExceededError(ValueError):
    """Raised when a customer exceeds the sliding-window order rate limit."""


class DownstreamServiceError(RuntimeError):
    """Raised when a downstream SaaS service (Billing or Slack) fails."""


_PRIORITY_RANK: Dict[str, int] = {
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
        self._confirmed_by_event_id: Dict[str, Dict[str, Any]] = {}

    def process_order(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an incoming order event across Inventory, Billing, and Slack."""
        event_id = event["event_id"]

        # REQ-0001: Replay-safe idempotency by event_id
        if event_id in self._confirmed_by_event_id:
            return dict(self._confirmed_by_event_id[event_id])

        sku = event["sku"]
        qty = event["qty"]
        customer_id = event["customer_id"]
        total_cents = event["total_cents"]
        timestamp = event.get("timestamp", 0)

        if qty <= 0:
            raise ValueError("qty must be positive")
        if self.stock.get(sku, 0) < qty:
            raise ValueError("insufficient stock")

        # REQ-0004: Sliding-window rate limit (max 3 confirmed orders within < 60s window)
        recent_customer_orders = [
            order
            for order in self.orders
            if order["customer_id"] == customer_id
            and 0 <= (timestamp - order.get("timestamp", 0)) < 60
        ]
        if len(recent_customer_orders) >= 3:
            raise RateLimitExceededError(
                f"Customer {customer_id} exceeded max 3 orders within 60s window"
            )

        # Decrement inventory and begin transactional section (REQ-0002)
        self.stock[sku] -= qty
        charge_added = False
        try:
            if event.get("simulate_billing_failure"):
                raise DownstreamServiceError("Billing gateway declined")

            charge = {
                "event_id": event_id,
                "customer_id": customer_id,
                "amount_cents": total_cents,
            }
            self.charges.append(charge)
            charge_added = True

            if event.get("simulate_slack_failure"):
                raise DownstreamServiceError("Slack webhook timeout")
        except DownstreamServiceError:
            self.stock[sku] += qty
            if charge_added:
                self.charges = [
                    c for c in self.charges if c.get("event_id") != event_id
                ]
            self.audit_log.append({"event_id": event_id, "status": "ROLLED_BACK"})
            raise

        # REQ-0003: Inclusive VIP threshold and priority escalation
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
        self._confirmed_by_event_id[event_id] = dict(record)
        self.audit_log.append({"event_id": event_id, "status": "CONFIRMED"})
        return dict(record)

    def list_pending_fulfillments(self) -> List[Dict[str, Any]]:
        """Returns confirmed orders sorted by HIGH -> MEDIUM -> LOW, preserving FIFO."""
        return [
            dict(order)
            for order in sorted(
                self.orders,
                key=lambda o: _PRIORITY_RANK.get(o.get("priority", "MEDIUM"), 1),
            )
        ]
