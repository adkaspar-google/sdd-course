# Sprint 1 Design Spec: OrderPulse Core Workflow (2026-10-01)

## Status
Approved (Sprint 1)

## Overview
OrderPulse coordinates incoming order events across `InventoryLedger`, `Billing`, `SlackNotifier`, and `OrdersDB`.

## Requirements
1. **Validation**:
   - `qty` must be strictly positive (`qty > 0`), otherwise raise `ValueError("qty must be positive")`.
   - `stock.get(sku, 0)` must be at least `qty`, otherwise raise `ValueError("insufficient stock")`.
2. **Slack Channel Routing**:
   - Route orders to `#vip-orders` when `total_cents > 100000`.
   - Route all other orders (`total_cents <= 100000`) to `#orders`.
3. **Rate Limiting**:
   - No customer rate limiting is enforced in Sprint 1.
4. **Fulfillment Listing**:
   - `list_pending_fulfillments()` returns confirmed orders in insertion order.
