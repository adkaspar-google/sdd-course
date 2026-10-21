# OrderPulse Living Specification (`order-pulse`)

## Overview
`OrderPulseEngine` coordinates multi-step order processing across `OrdersDB`, `Billing`, `InventoryLedger`, and `SlackNotifier` as a single living specification (`OpenSpec` SSOT) merged across Sprints 1–3.

## Functional Requirements

### REQ-0001: Replay-Safe Event Idempotency
- **WHEN** `process_order(event)` is called with an `event_id` that has already been confirmed
- **THEN** the engine SHALL return a copy of the existing confirmed order record without re-decrementing `stock`, appending a duplicate charge to `charges`, emitting a duplicate Slack notification to `slack_messages`, or appending a duplicate entry to `audit_log`.

### REQ-0002: Transactional Rollback Across Inventory, Billing, and Slack
- **WHEN** `simulate_billing_failure` or `simulate_slack_failure` is truthy on the incoming event
- **THEN** the engine SHALL raise `DownstreamServiceError`, restore `self.stock[sku]` to its pre-order quantity, remove any partial charge for that `event_id` from `self.charges`, and append `{"event_id": event["event_id"], "status": "ROLLED_BACK"}` to `self.audit_log`.

### REQ-0003: Inclusive VIP Order Routing and Priority Escalation
- **WHEN** an incoming order has `total_cents >= 100000`
- **THEN** the engine SHALL route the notification and order record to `channel = "#vip-orders"` and escalate `priority = "HIGH"`; otherwise it SHALL route to `channel = "#orders"` and preserve `event.get("priority", "MEDIUM")`.

### REQ-0004: Customer Sliding-Window Rate Limiting
- **WHEN** a customer (`customer_id`) already has 3 confirmed orders with `timestamp - prev_ts < 60` (and `timestamp >= prev_ts`)
- **THEN** the engine SHALL raise `RateLimitExceededError` before mutating inventory, billing, or Slack state.

### REQ-0005: Priority-Sorted Pending Fulfillment Queue
- **WHEN** `list_pending_fulfillments()` is invoked
- **THEN** it SHALL return confirmed orders ordered by priority tier (`HIGH` -> `MEDIUM` -> `LOW`) while preserving FIFO arrival order within each priority tier.

## Out of Scope (Strict Scope Guard)
- Promotional discount calculation (`apply_promo_discount`) is strictly out of scope.
- CSV export generation (`export_csv`) is strictly out of scope.
