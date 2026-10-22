# Conductor Track Plan — Milestone 1 (M1: Greenfield Core Ledger)

## 5-Step Scorecard
| Step | Dimension | Target | Verification Gate | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **OpenSpec Delta Staging & Merge** | Stage `ADDED` requirements in `openspec/changes/m1/specs/ledger-flow/spec.md`, merge into `openspec/specs/ledger-flow/spec.md`, and archive to `openspec/changes/archive/m1/` | Zero contradictions in living spec | `[x]` |
| 2 | **8-Section `SPEC.md` SSOT Sync** | Synchronize all 8 canonical sections in `SPEC.md` for M1 core ledger rules | All 8 sections present & consistent | `[x]` |
| 3 | **Account Lifecycle (`open_account`, `get_balance`)** | Trimmed non-empty `account_id`, currency in `{'USD', 'EUR', 'GBP'}`, `initial_cents >= 0`, `ValueError` on invalid/duplicate, `KeyError` on unknown balance lookup | Unit tests for valid & invalid inputs | `[x]` |
| 4 | **Transfer Engine (`post_transfer`)** | Same-currency transfer (`amount_cents > 0`), flat `1%` fee (`amount_cents // 100`) debited immediately from `from_acct`, `PENDING` if `amount_cents > 100000` else `SETTLED` | Unit tests for boundary `100000` vs `100001`, fees, and insufficient funds | `[x]` |
| 5 | **Locked Regression Suite Verification** | Full `unittest` suite in `test_ledger_flow.py` passing with exit code 0 | `python3 -m unittest` exits 0 | `[x]` |

## Task Breakdown
- [x] **Task 1.1**: Author M1 OpenSpec delta and merge into canonical `openspec/specs/ledger-flow/spec.md`.
- [x] **Task 1.2**: Author 8-Section `SPEC.md` Single Source of Truth.
- [x] **Task 1.3**: Implement `LedgerFlow.open_account`, `LedgerFlow.get_balance`, and `LedgerFlow.post_transfer` in `ledger_flow.py`.
- [x] **Task 1.4**: Implement locked unit test suite in `test_ledger_flow.py` covering happy paths, fee calculation, `100000` vs `100001` threshold, and error contracts (`ValueError`, `KeyError`).

## Out of Scope (Milestone 1)
- Clearing or canceling `'PENDING'` transfers (deferred to subsequent milestones).
- Tiered or dynamic fee schedules beyond the M1 flat `1%` (`amount_cents // 100`) fee.
- Cross-currency FX conversion transfers.
- Persistence to external databases or filesystems.
