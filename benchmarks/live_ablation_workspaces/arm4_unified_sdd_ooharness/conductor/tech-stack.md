# Conductor Constitutional Tech-Stack Governance (`conductor/tech-stack.md`)

## 1. Runtime & Language Constraints
- **Language**: Python 3.10+ (strict standard library only: `typing`, `unittest`).
- **Zero External Dependencies**: No third-party packages or network calls permitted.
- **Type Safety**: Complete PEP 484 type annotations required across all public classes and methods.

## 2. Architectural Invariants (`OO-Harness`)
- **Active Harness Subclasses**: `MultiAppWorkflowHarness` + `DriftRemediationHarness`.
- **State Machine Atomicity**: Every multi-app mutation across `stock`, `charges`, `slack_messages`, `orders`, and `audit_log` must be atomic; downstream failures (`simulate_billing_failure`, `simulate_slack_failure`) must compensate/roll back prior state mutations and record `{"event_id": ..., "status": "ROLLED_BACK"}` in `audit_log`.
- **Verifier Integrity**: `test_order_pulse.py` is locked read-only (`chmod 444`) prior to actuation and verified before completion.
- **Zero Speculative Bloat**: Unrequested methods (`apply_promo_discount`, `export_csv`) and `# TODO` placeholders are strictly forbidden.
