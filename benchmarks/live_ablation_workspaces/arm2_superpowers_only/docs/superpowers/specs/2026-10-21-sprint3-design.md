# Sprint 3 Design Spec: VIP Boundary Update, Rate Limiting & Priority Queue (2026-10-21)

## Status
Approved (Sprint 3)

## Overview
Updates the VIP routing threshold to inclusive `>= 100000`, introduces a per-customer sliding-window rate limit, and sorts pending fulfillments by priority.

## Requirements
1. **Inclusive VIP Threshold & Priority Upgrade**:
   - Route orders to `#vip-orders` when `total_cents >= 100000` (otherwise `#orders`).
   - Automatically set `priority = "HIGH"` whenever `total_cents >= 100000`.
2. **Sliding-Window Rate Limit (3 Orders per 60s)**:
   - For a given `customer_id` at `timestamp = T`, count confirmed orders for that customer whose `timestamp` satisfies `T - 60 <= order.timestamp <= T` (or within 60 seconds sliding window `abs(T - order.timestamp) <= 60` / `0 <= T - order.timestamp <= 60`).
   - If the customer already has 3 confirmed orders in the 60-second window, raise `RateLimitExceededError` before mutating inventory, billing, or Slack.
3. **Priority Queue Sorting in `list_pending_fulfillments()`**:
   - Sort confirmed orders by priority tier `HIGH -> MEDIUM -> LOW` (preserving relative order or timestamp within each tier).
