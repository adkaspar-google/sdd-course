# Conductor Track Plan — Milestone 3 (M3: Requirement Rename & Tiered Fee Mutation)

## 5-Step Scorecard
| Step | Dimension | Target | Verification Gate | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **OpenSpec Delta Staging & Merge** | Stage M3 `ADDED`, `MODIFIED`, `REMOVED`, `RENAMED` deltas in `openspec/changes/m3/specs/ledger-flow/spec.md`, merge into `openspec/specs/ledger-flow/spec.md`, archive to `openspec/changes/archive/m3/` | Zero stale `'PENDING'` or flat-fee contradictions in living spec | `[x]` |
| 2 | **8-Section `SPEC.md` SSOT Sync** | Update all 8 canonical sections in `SPEC.md` with `'AWAITING_CLEARING'`, `clear_transfer` (`settle_pending` alias), inclusive `100000` threshold, tiered fees (50 bps / 100 bps, 10c floor), and replay-safe idempotency | All 8 sections present & consistent | `[x]` |
| 3 | **Rename & Tiered Fee Engine** | Rename `'PENDING'` to `'AWAITING_CLEARING'`, implement `clear_transfer` + `settle_pending` alias, inclusive `>= 100000` hold, and tiered fee with 10-cent minimum floor | Unit tests for `< 100000` (100 bps, 10c floor) and `>= 100000` (50 bps, `'AWAITING_CLEARING'`) | `[x]` |
| 4 | **Replay-Safe Idempotency (`post_transfer`)** | Return copy of existing transfer on identical `(tx_id, from_acct, to_acct, amount_cents)` without re-debiting; raise `ValueError('Conflicting tx_id')` on mismatch | Unit tests for idempotent replay and conflicting `tx_id` | `[x]` |
| 5 | **Locked Regression Suite Verification** | Full `unittest` suite in `test_ledger_flow.py` updated for M3 rules and passing with exit code 0 | `python3 -m unittest` exits 0 | `[x]` |

## Task Breakdown
- [x] **Task 3.1**: Stage M3 OpenSpec delta (`ADDED`, `MODIFIED`, `REMOVED`, `RENAMED`), merge into canonical `openspec/specs/ledger-flow/spec.md`, and archive under `openspec/changes/archive/m3/`.
- [x] **Task 3.2**: Synchronize 8-Section `SPEC.md` Single Source of Truth to reflect M3 renames, tiered fees, and idempotency with zero contradictions.
- [x] **Task 3.3**: Update `LedgerFlow` in `ledger_flow.py` with `'AWAITING_CLEARING'`, `clear_transfer` (and `settle_pending` alias), inclusive `100000` threshold, tiered fee schedule with 10-cent floor, and replay-safe idempotency.
- [x] **Task 3.4**: Update and expand locked unit test suite in `test_ledger_flow.py` to verify all M1–M3 behaviors.

## Out of Scope (Milestone 3)
- Canceling or reversing `'AWAITING_CLEARING'` or `'SETTLED'` transfers with refund/fee-refund semantics (deferred to subsequent milestones).
- Cross-currency FX conversion transfers.
- External database persistence.
