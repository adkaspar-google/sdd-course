# Conductor Track Plan: `order_pulse_01`

## 5-Step Scorecard (`DriftRemediationHarness` + `MultiAppWorkflowHarness`)

| Step | Dimension | Specification Contract |
| :--- | :--- | :--- |
| **1. Inputs** | `event: Dict[str, Any]`, `initial_stock: Optional[Dict[str, int]]` | Keys: `event_id`, `customer_id`, `sku`, `qty`, `total_cents`, optional `priority` (default `"MEDIUM"`), optional `timestamp` (default `0`), optional `simulate_billing_failure`, optional `simulate_slack_failure`. |
| **2. Outputs** | `Dict[str, Any]` (`process_order`), `List[Dict[str, Any]]` (`list_pending_fulfillments`) | Confirmed record copy with `status: "CONFIRMED"`, routed `channel`, effective `priority`, and deterministic `HIGH -> MEDIUM -> LOW` FIFO queue ordering. |
| **3. State Transitions** | `stock`, `charges`, `slack_messages`, `orders`, `audit_log` | Idempotent short-circuit on duplicate confirmed `event_id`; transactional rollback of `stock` and `charges` plus `ROLLED_BACK` audit entry on billing/Slack errors. |
| **4. Error Contracts** | `ValueError`, `RateLimitExceededError`, `DownstreamServiceError` | `ValueError` on `qty <= 0` or `stock < qty`; `RateLimitExceededError` when `>= 3` confirmed orders exist in `0 <= ts - prev_ts <= 60`; `DownstreamServiceError` on simulated downstream failures. |
| **5. Out of Scope** | `Out of Scope: apply_promo_discount, export_csv` | Strictly prohibit `apply_promo_discount`, `export_csv`, and any `# TODO` comments in `order_pulse.py`. |

---

## Bite-Sized TDD Execution Plan (`@socratic-brainstorming` -> `@systematic-debugging-gate` -> `@subagent-two-stage-review` -> `@verification-before-completion`)

- [x] **Task 1 (`REQ-0001`..`REQ-0005` Spec Sync)**: Author living RFC 2119 + Gherkin specification in `openspec/specs/order-pulse/spec.md` and 8-section `SPEC.md`.
- [x] **Task 2 (Adversarial Red-Phase Test Suite + Lock)**: Write boundary & equivalence tests in `test_order_pulse.py` and lock with `chmod 444 test_order_pulse.py`.
- [x] **Task 3 (Stateless Builder Actuation)**: Remediate drift and implement `REQ-0001` through `REQ-0005` in `order_pulse.py`.
- [x] **Task 4 (Two-Stage Cold Audit & Verification Gate)**: Execute `python3 -m unittest discover` and verify 100% pass rate and intact read-only test lock.
