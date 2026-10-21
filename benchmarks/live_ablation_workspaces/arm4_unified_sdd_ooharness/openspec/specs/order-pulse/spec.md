# Specification: `order-pulse` Multi-App Workflow Engine

> **SSOT Status**: Living Specification (`openspec/specs/order-pulse/spec.md`)
> **Harness Archetypes**: `MultiAppWorkflowHarness` + `DriftRemediationHarness` (`OO-Harness`)
> **RFC 2119 Normative Keywords**: `MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`

---

## Requirement `[REQ-0001]`: Event Idempotency & Deduplication
The `OrderPulseEngine.process_order(event)` method **MUST** enforce strict event idempotency keyed by `event["event_id"]`.
If an order with `event["event_id"]` has already been confirmed in `self.orders`, `process_order` **MUST** immediately return a shallow copy (`dict(existing_record)`) of the previously confirmed order record and **MUST NOT** mutate `self.stock`, `self.charges`, `self.slack_messages`, `self.orders`, or `self.audit_log`, nor re-run rate-limit or stock deductions.

```gherkin
Feature: REQ-0001 Event Idempotency
  Scenario: Duplicate confirmed event_id returns existing record without side effects
    Given an OrderPulseEngine initialized with stock {"SKU-1": 10}
    And order event "evt-100" for customer "cust-1" with qty 2 and total_cents 5000 is confirmed
    When the identical or replayed event with event_id "evt-100" is submitted again
    Then process_order MUST return a copy of the original confirmed record for "evt-100"
    And stock["SKU-1"] MUST remain 8
    And len(charges), len(slack_messages), len(orders), and len(audit_log) MUST remain 1
```

---

## Requirement `[REQ-0002]`: Pre-Mutation Validation & Transactional Rollback
`OrderPulseEngine.process_order(event)` **MUST** validate `event["qty"] > 0`, `self.stock.get(sku, 0) >= qty`, and the customer sliding-window rate limit **BEFORE** mutating any state (`stock`, `charges`, `slack_messages`, `orders`, `audit_log`).
When `simulate_billing_failure` or `simulate_slack_failure` is truthy during processing, the engine **MUST** atomically roll back any in-flight mutations to `self.stock[sku]` and `self.charges` so zero partial state remains, **MUST** append `{"event_id": event["event_id"], "status": "ROLLED_BACK"}` to `self.audit_log`, and **MUST** raise `DownstreamServiceError`.

```gherkin
Feature: REQ-0002 Transactional Compensation & Rollback
  Scenario: Billing gateway failure rolls back stock and logs ROLLED_BACK
    Given an OrderPulseEngine initialized with stock {"SKU-1": 5}
    When an order event "evt-fail-bill" with qty 3 and simulate_billing_failure=True is processed
    Then DownstreamServiceError MUST be raised
    And stock["SKU-1"] MUST remain 5
    And charges, slack_messages, and orders MUST be empty
    And audit_log MUST contain [{"event_id": "evt-fail-bill", "status": "ROLLED_BACK"}]

  Scenario: Slack webhook failure rolls back stock and billing charge and logs ROLLED_BACK
    Given an OrderPulseEngine initialized with stock {"SKU-1": 5}
    When an order event "evt-fail-slack" with qty 2 and simulate_slack_failure=True is processed
    Then DownstreamServiceError MUST be raised
    And stock["SKU-1"] MUST remain 5
    And charges, slack_messages, and orders MUST be empty
    And audit_log MUST contain [{"event_id": "evt-fail-slack", "status": "ROLLED_BACK"}]
```

---

## Requirement `[REQ-0003]`: VIP Routing & Priority Promotion
If `event["total_cents"] >= 100000` (inclusive boundary `100000` cents = `$1,000.00`), `OrderPulseEngine.process_order(event)` **MUST** route the notification to `channel = "#vip-orders"` and **MUST** promote the order and Slack message `priority` to `"HIGH"` regardless of the input `event.get("priority")`.
If `event["total_cents"] < 100000` (e.g., `99999`), the engine **MUST** route to `channel = "#orders"` and preserve `event.get("priority", "MEDIUM")`.

```gherkin
Feature: REQ-0003 VIP Threshold Routing and Priority Promotion
  Scenario: Exact boundary total_cents == 100000 promotes to HIGH and #vip-orders
    Given an OrderPulseEngine initialized with stock {"SKU-1": 10}
    When an order with total_cents 100000 and priority "LOW" is processed
    Then the confirmed order and slack_message MUST have channel "#vip-orders" and priority "HIGH"

  Scenario: Immediately below boundary total_cents == 99999 routes to #orders
    Given an OrderPulseEngine initialized with stock {"SKU-1": 10}
    When an order with total_cents 99999 and priority "LOW" is processed
    Then the confirmed order and slack_message MUST have channel "#orders" and priority "LOW"
```

---

## Requirement `[REQ-0004]`: Sliding-Window Customer Rate Limit
Before mutating state for a new `event_id`, `OrderPulseEngine.process_order(event)` **MUST** count confirmed orders in `self.orders` for `event["customer_id"]` where `0 <= event.get("timestamp", 0) - prev["timestamp"] <= 60` (inclusive 60-second window).
If `3` or more confirmed orders exist within that window, `process_order` **MUST** raise `RateLimitExceededError` immediately with zero side effects on `stock`, `charges`, `slack_messages`, `orders`, or `audit_log`. Rolled-back or rejected events **MUST NOT** count toward the customer rate limit.

```gherkin
Feature: REQ-0004 Sliding-Window Rate Limit
  Scenario: 4th order at exact 60-second boundary is rejected with zero side effects
    Given customer "cust-rate" has 3 confirmed orders at timestamps 100, 120, and 150
    When customer "cust-rate" submits a 4th order at timestamp 160 (160 - 100 == 60)
    Then RateLimitExceededError MUST be raised
    And no stock, charge, slack_message, order, or audit_log entry is added

  Scenario: 4th order at 61-second boundary succeeds once oldest order exits window
    Given customer "cust-rate" has 3 confirmed orders at timestamps 100, 120, and 150
    When customer "cust-rate" submits a 4th order at timestamp 161 (161 - 100 == 61)
    Then the order MUST be confirmed with status "CONFIRMED"
```

---

## Requirement `[REQ-0005]`: Priority Queue Ordering & Out-of-Scope Guard
`OrderPulseEngine.list_pending_fulfillments()` **MUST** return copies of all confirmed orders sorted deterministically by priority tier `HIGH -> MEDIUM -> LOW`, while strictly preserving FIFO insertion order within each priority tier.
In accordance with the Conductor 5-Step Scorecard `Out of Scope` guard, `OrderPulseEngine` **MUST NOT** contain unrequested speculative methods (`apply_promo_discount`, `export_csv`) or legacy `# TODO` comments.

```gherkin
Feature: REQ-0005 Deterministic Priority Queue with FIFO Stability
  Scenario: Mixed priority orders are returned in HIGH -> MEDIUM -> LOW order with FIFO stability
    Given confirmed orders inserted in sequence: LOW(e1), MEDIUM(e2), HIGH(e3), MEDIUM(e4), HIGH(e5), LOW(e6)
    When list_pending_fulfillments() is called
    Then the returned event_ids MUST be ["e3", "e5", "e2", "e4", "e1", "e6"]
```
