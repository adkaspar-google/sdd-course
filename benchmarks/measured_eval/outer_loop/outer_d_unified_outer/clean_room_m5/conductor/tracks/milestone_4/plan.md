# Conductor Track Plan — Milestone 4 (M4: Reversals & Constitutional Scope Governance)

## 5-Step Scorecard
| Step | Dimension | Target | Verification Gate | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **OpenSpec Delta Staging & Merge** | Stage M4 `ADDED` & `MODIFIED` deltas in `openspec/changes/m4/specs/ledger-flow/spec.md`, merge into `openspec/specs/ledger-flow/spec.md`, archive to `openspec/changes/archive/m4/` | Zero contradictions in living spec | `[x]` |
| 2 | **8-Section `SPEC.md` SSOT Sync** | Update all 8 canonical sections in `SPEC.md` with `reverse_transfer`, `total_collected_fees`, and no-overdraft constitutional invariants | All 8 sections present & consistent | `[x]` |
| 3 | **Transfer Reversal Engine (`reverse_transfer`)** | Refund `amount_cents + fee_cents` to `from_acct`; debit `amount_cents` from `to_acct` if `'SETTLED'` (raising `ValueError('Recipient has insufficient funds to reverse')` if `to_acct` balance `< amount_cents`); raise `KeyError` on unknown `tx_id` and `ValueError` if already `'REVERSED'` | Unit tests for `'AWAITING_CLEARING'` reversal, `'SETTLED'` reversal, low recipient balance, and double reversal | `[x]` |
| 4 | **Fee Revenue Aggregation (`total_collected_fees`)** | Sum `fee_cents` across non-reversed (`'SETTLED'` or `'AWAITING_CLEARING'`) transfers for `currency` | Unit tests across currencies before & after reversals | `[x]` |
| 5 | **Locked Regression Suite Verification** | Full M1–M4 `unittest` suite in `test_ledger_flow.py` passing with exit code 0 | `python3 -m unittest` exits 0 | `[x]` |

## Task Breakdown
- [x] **Task 4.1**: Stage M4 OpenSpec delta (`ADDED`, `MODIFIED`), merge into canonical `openspec/specs/ledger-flow/spec.md`, and archive under `openspec/changes/archive/m4/`.
- [x] **Task 4.2**: Synchronize 8-Section `SPEC.md` Single Source of Truth for M4 reversals and fee aggregation.
- [x] **Task 4.3**: Implement `LedgerFlow.reverse_transfer` and `LedgerFlow.total_collected_fees` in `ledger_flow.py` while preserving strict no-overdraft checks.
- [x] **Task 4.4**: Expand locked unit test suite in `test_ledger_flow.py` to verify M4 reversals, recipient insufficient-funds guard, fee aggregation, and overdraft prohibition.

## Out of Scope (Milestone 4)
- Overdraft lines of credit or negative account balances (strictly prohibited by constitutional scope governance).
- Cross-currency FX conversion transfers or multi-currency consolidated fee conversion.
- Partial transfer reversals.
