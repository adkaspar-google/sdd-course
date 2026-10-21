"""OrderPulse multi-app workflow engine implementing REQ-0001 through REQ-0005."""

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

    def process_order(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an incoming order event across Inventory, Billing, and Slack."""
        event_id = event["event_id"]

        # REQ-0001: Idempotency on already-confirmed event_id
        for existing in self.orders:
            if existing["event_id"] == event_id:
                return dict(existing)

        sku = event["sku"]
        qty = event["qty"]
        if qty <= 0:
            raise ValueError("qty must be positive")
        if self.stock.get(sku, 0) < qty:
            raise ValueError("insufficient stock")

        # REQ-0004: Sliding-window rate limit (inclusive 60s window, max 3 confirmed orders)
        customer_id = event["customer_id"]
        current_ts = event.get("timestamp", 0)
        recent_customer_orders = sum(
            1
            for prev in self.orders
            if prev["customer_id"] == customer_id
            and 0 <= current_ts - prev.get("timestamp", 0) <= 60
        )
        if recent_customer_orders >= 3:
            raise RateLimitExceededError(
                f"Customer {customer_id} exceeded rate limit of 3 orders within 60s"
            )

        # REQ-0002: Transactional execution with rollback on downstream service failure
        previous_stock = self.stock[sku]
        charges_snapshot_len = len(self.charges)
        try:
            self.stock[sku] = previous_stock - qty
            if event.get("simulate_billing_failure"):
                raise DownstreamServiceError("Billing gateway declined")

            charge = {
                "event_id": event_id,
                "customer_id": customer_id,
                "amount_cents": event["total_cents"],
            }
            self.charges.append(charge)

            if event.get("simulate_slack_failure"):
                raise DownstreamServiceError("Slack webhook timeout")
        except DownstreamServiceError:
            self.stock[sku] = previous_stock
            del self.charges[charges_snapshot_len:]
            self.audit_log.append(
                {"event_id": event_id, "status": "ROLLED_BACK"}
            )
            raise

        # REQ-0003: VIP routing and priority promotion at exact inclusive >= 100000 boundary
        total_cents = event["total_cents"]
        if total_cents >= 100000:
            channel = "#vip-orders"
            priority = "HIGH"
        else:
            channel = "#orders"
            priority = event.get("priority", "MEDIUM")

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
            "timestamp": current_ts,
            "channel": channel,
            "status": "CONFIRMED",
        }
        self.orders.append(record)
        self.audit_log.append({"event_id": event_id, "status": "CONFIRMED"})
        return dict(record)

    def list_pending_fulfillments(self) -> List[Dict[str, Any]]:
        """Returns confirmed orders sorted by HIGH -> MEDIUM -> LOW with FIFO stability."""
        indexed_orders = list(enumerate(self.orders))
        indexed_orders.sort(
            key=lambda item: (
                _PRIORITY_RANK.get(item[1].get("priority", "MEDIUM"), 1),
                item[0],
            )
        )
        return [dict(order) for _, order in indexed_orders]
