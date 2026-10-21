# Conductor Track Plan: `order_pulse_01`

## Track Metadata
- **Track ID**: `order_pulse_01`
- **Spec Reference**: `openspec/specs/order-pulse/spec.md`
- **Architecture Mode**: Flat Outer-Loop SDD (`OpenSpec` + `Conductor` without Inner-Loop Superpowers or `OO-Harness`)

## Tasks
- [x] **Task 1 (`REQ-0001`)**: Add replay-safe `event_id` idempotency lookup in `OrderPulseEngine.process_order`.
- [x] **Task 2 (`REQ-0004`)**: Enforce per-customer sliding-window rate limit (max 3 confirmed orders within `timestamp - prev_ts < 60`).
- [x] **Task 3 (`REQ-0002`)**: Implement transactional rollback across `stock`, `charges`, and `audit_log` when `simulate_billing_failure` or `simulate_slack_failure` occurs.
- [x] **Task 4 (`REQ-0003`)**: Update VIP threshold to `total_cents >= 100000` with `channel = "#vip-orders"` and `priority = "HIGH"`.
- [x] **Task 5 (`REQ-0005`)**: Sort `list_pending_fulfillments()` by `HIGH -> MEDIUM -> LOW` preserving FIFO order within each priority tier, and remove legacy out-of-scope TODOs (`apply_promo_discount`, `export_csv`).
- [x] **Task 6**: Verify with `test_order_pulse.py` via `python3 -m unittest`.
