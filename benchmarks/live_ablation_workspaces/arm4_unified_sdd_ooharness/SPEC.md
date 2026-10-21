# `SPEC.md` — OrderPulse Multi-App Workflow Engine (8-Section Rebuildable SSOT)

## 1. System Overview & Purpose
`OrderPulseEngine` coordinates multi-application order processing across an Inventory Ledger (`stock`), Billing Gateway (`charges`), Slack Notifier (`slack_messages`), Orders Database (`orders`), and Compliance Audit Log (`audit_log`). It guarantees event idempotency, sliding-window rate limiting, transactional rollback on downstream failure, VIP threshold routing, and priority-queue fulfillment ordering.

## 2. Domain Model & Data Schemas
- **Order Event Input (`Dict[str, Any]`)**:
  - `event_id: str` (required)
  - `customer_id: str` (required)
  - `sku: str` (required)
  - `qty: int` (required, must be `> 0`)
  - `total_cents: int` (required)
  - `priority: str` (optional, default `"MEDIUM"`, domain `{"HIGH", "MEDIUM", "LOW"}`)
  - `timestamp: int` (optional, default `0`)
  - `simulate_billing_failure: bool` (optional, default `False`)
  - `simulate_slack_failure: bool` (optional, default `False`)
- **Confirmed Order Record (`Dict[str, Any]`)**:
  - `event_id`, `customer_id`, `sku`, `qty`, `total_cents`, `priority`, `timestamp`, `channel`, `status: "CONFIRMED"`
- **Charge Record (`Dict[str, Any]`)**:
  - `{"event_id": str, "customer_id": str, "amount_cents": int}`
- **Slack Message Record (`Dict[str, Any]`)**:
  - `{"event_id": str, "channel": str, "priority": str}`
- **Audit Log Record (`Dict[str, Any]`)**:
  - `{"event_id": str, "status": "CONFIRMED" | "ROLLED_BACK"}`

## 3. Public Interface & Signatures
- `class RateLimitExceededError(ValueError)`
- `class DownstreamServiceError(RuntimeError)`
- `class OrderPulseEngine`:
  - `__init__(self, initial_stock: Optional[Dict[str, int]] = None) -> None`
  - `process_order(self, event: Dict[str, Any]) -> Dict[str, Any]`
  - `list_pending_fulfillments(self) -> List[Dict[str, Any]]`

## 4. Normative Behavioral Requirements (`REQ-0001`..`REQ-0005`)
- **`REQ-0001` (Idempotency)**: If `event["event_id"]` already exists in `self.orders`, return `dict(existing_record)` immediately with zero state mutations.
- **`REQ-0002` (Transactional Rollback)**: Validate `qty > 0`, `stock.get(sku, 0) >= qty`, and customer rate limit prior to mutating state. If `simulate_billing_failure` or `simulate_slack_failure` occurs, restore `self.stock[sku]` and `self.charges` to their exact pre-event values, append `{"event_id": event["event_id"], "status": "ROLLED_BACK"}` to `self.audit_log`, and raise `DownstreamServiceError`.
- **`REQ-0003` (VIP Routing & Priority Promotion)**: If `event["total_cents"] >= 100000`, set `channel = "#vip-orders"` and `priority = "HIGH"`; else set `channel = "#orders"` and `priority = event.get("priority", "MEDIUM")`.
- **`REQ-0004` (Sliding-Window Rate Limit)**: Count confirmed orders for `event["customer_id"]` satisfying `0 <= event.get("timestamp", 0) - prev["timestamp"] <= 60`. If count `>= 3`, raise `RateLimitExceededError` with zero side effects.
- **`REQ-0005` (Priority Queue & Out-of-Scope Guard)**: `list_pending_fulfillments()` returns confirmed orders sorted by `HIGH -> MEDIUM -> LOW` preserving FIFO insertion order within each tier. `apply_promo_discount` and `export_csv` are strictly out of scope and must not exist.

## 5. Error Handling & Compensation Matrix
| Failure Condition | Exception Raised | `stock` / `charges` / `orders` / `slack_messages` Mutation | `audit_log` Mutation |
| :--- | :--- | :--- | :--- |
| `qty <= 0` or `stock < qty` | `ValueError` | None | None |
| `>= 3` confirmed orders in `[ts - 60, ts]` | `RateLimitExceededError` | None | None |
| `simulate_billing_failure == True` | `DownstreamServiceError` | Rolled back (None net) | Appends `{"event_id": ..., "status": "ROLLED_BACK"}` |
| `simulate_slack_failure == True` | `DownstreamServiceError` | Rolled back (None net) | Appends `{"event_id": ..., "status": "ROLLED_BACK"}` |

## 6. Boundary Conditions & Equivalence Classes
- VIP boundary: `total_cents == 100000` (`#vip-orders`, `"HIGH"`) vs. `total_cents == 99999` (`#orders`, original priority).
- Rate-limit window boundary: `ts - prev_ts == 60` (included in window, blocks 4th order) vs. `ts - prev_ts == 61` (expired from window, allows 4th order).
- Failed/rolled-back orders do not count toward the 3-order sliding window.

## 7. Out-of-Scope & Anti-Bloat Constraints
- `Out of Scope: apply_promo_discount, export_csv`
- No `# TODO` comments or unrequested helper methods on `OrderPulseEngine`.

## 8. Verification & Acceptance Criteria
- 100% pass rate on locked `test_order_pulse.py` via `python3 -m unittest discover`.
