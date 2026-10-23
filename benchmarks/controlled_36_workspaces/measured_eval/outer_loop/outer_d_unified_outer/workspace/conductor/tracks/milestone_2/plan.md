# Conductor Track Plan — Milestone 2 (M2: Clearing & Account Statements)

## 5-Step Scorecard
| Step | Dimension | Target | Verification Gate | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **OpenSpec Delta Staging & Merge** | Stage M2 `ADDED` & `MODIFIED` requirements in `openspec/changes/m2/specs/ledger-flow/spec.md`, merge into `openspec/specs/ledger-flow/spec.md`, archive to `openspec/changes/archive/m2/` | Zero contradictions with M1 | `[x]` |
| 2 | **8-Section `SPEC.md` SSOT Sync** | Update all 8 canonical sections in `SPEC.md` with `settle_pending` and `account_statement` contracts and state transitions | All 8 sections present & consistent | `[x]` |
| 3 | **Pending Clearing (`settle_pending`)** | Transition `'PENDING'` transfer to `'SETTLED'`, credit `amount_cents` to `to_acct`, `KeyError` on unknown `tx_id`, `ValueError` if not `'PENDING'` | Unit tests for valid settle, double settle, settled tx, unknown tx | `[x]` |
| 4 | **Account Statements (`account_statement`)** | Return copies of transfers where `from_acct == account_id` or `to_acct == account_id` sorted by `(timestamp, insertion_index)` ascending, `KeyError` on unknown `account_id` | Unit tests for sorting, tie-breaking, defensive copy isolation, unknown acct | `[x]` |
| 5 | **Locked Regression Suite Verification** | Full M1 + M2 `unittest` suite in `test_ledger_flow.py` passing with exit code 0 | `python3 -m unittest` exits 0 | `[x]` |

## Task Breakdown
- [x] **Task 2.1**: Stage M2 OpenSpec delta, merge into canonical `openspec/specs/ledger-flow/spec.md`, and archive under `openspec/changes/archive/m2/`.
- [x] **Task 2.2**: Synchronize 8-Section `SPEC.md` Single Source of Truth for M1 + M2.
- [x] **Task 2.3**: Implement `LedgerFlow.settle_pending` and `LedgerFlow.account_statement` in `ledger_flow.py`.
- [x] **Task 2.4**: Extend locked unit test suite in `test_ledger_flow.py` with M2 clearing and statement tests while preserving all M1 tests.

## Out of Scope (Milestone 2)
- Canceling or reversing `'PENDING'` or `'SETTLED'` transfers (deferred to subsequent milestones).
- Tiered or dynamic fee schedules beyond the flat `1%` (`amount_cents // 100`) fee.
- Cross-currency FX conversion transfers.
