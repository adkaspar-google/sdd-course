# Sprint 2 Design Spec: Idempotency and Transactional Rollback (2026-10-10)

## Status
Approved (Sprint 2)

## Overview
Adds idempotent replay protection by `event_id` and atomic rollback across Inventory, Billing, and Slack when downstream services fail.

## Requirements
1. **Idempotency by `event_id`**:
   - If an incoming `event["event_id"]` has already been confirmed in `self.orders`, return a copy of the existing confirmed order record immediately without re-decrementing stock, re-charging billing, or re-sending Slack notifications.
2. **Transactional Rollback on Downstream Failure**:
   - If `simulate_billing_failure` or `simulate_slack_failure` is truthy, raise `DownstreamServiceError`.
   - Ensure `self.stock`, `self.charges`, `self.slack_messages`, and `self.orders` are rolled back to their pre-event state so no partial state leaks on failure.
