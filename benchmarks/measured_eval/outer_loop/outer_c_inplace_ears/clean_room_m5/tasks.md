# LedgerFlow — Implementation Tasks

## Milestone 1 (M1 — Greenfield Core Ledger)
- [x] **Task 1.1**: Specify EARS requirements (`WHEN <trigger> THE SYSTEM SHALL <response>`) in `requirements.md` for `open_account`, `get_balance`, and `post_transfer`.
- [x] **Task 1.2**: Document M1 data models, validation order, fee formula, and pending/settled state rules in `design.md`.
- [x] **Task 1.3**: Implement `open_account` and `get_balance` in `ledger_flow.py`.
- [x] **Task 1.4**: Implement `post_transfer` in `ledger_flow.py` with 1% flat fee (`amount_cents // 100`) and `100000` cents pending threshold.
- [x] **Task 1.5**: Write comprehensive unit tests in `test_ledger_flow.py` and verify all tests pass via `python3 -m unittest`.

## Milestone 2 (M2 — Clearing & Account Statements)
- [x] **Task 2.1**: Add EARS requirements REQ-M2-001 through REQ-M2-005 in `requirements.md` for `settle_pending` and `account_statement`.
- [x] **Task 2.2**: Update `design.md` with pending-to-settled clearing mechanics and `(timestamp, insertion_index)` statement ordering.
- [x] **Task 2.3**: Implement `settle_pending(tx_id)` and `account_statement(account_id)` in `ledger_flow.py`.
- [x] **Task 2.4**: Add M2 unit tests in `test_ledger_flow.py` covering clearing, double-settlement errors, unknown IDs, statement sorting, and defensive copy isolation.

## Milestone 3 (M3 — Requirement Rename & Tiered Fee Mutation)
- [x] **Task 3.1**: Update `requirements.md` in-place to rename `'PENDING'` to `'AWAITING_CLEARING'`, rename `settle_pending` to `clear_transfer` (with alias), update threshold to `>= 100000`, specify tiered fees with 10-cent floor, and add REQ-M3-001/REQ-M3-002 for replay-safe idempotency.
- [x] **Task 3.2**: Update `design.md` in-place with M3 fee tiers, inclusive `100000` threshold, `AWAITING_CLEARING` state machine, and idempotency gate.
- [x] **Task 3.3**: Update `ledger_flow.py` with `clear_transfer` (plus `settle_pending` alias), `'AWAITING_CLEARING'`, tiered fees, and `tx_id` idempotency / conflict detection.
- [x] **Task 3.4**: Update and expand `test_ledger_flow.py` for M3 semantics and verify via `python3 -m unittest`.

## Milestone 4 (M4 — Reversals & Constitutional Scope Governance)
- [x] **Task 4.1**: Add EARS requirements REQ-M4-001 through REQ-M4-006 in `requirements.md` for `reverse_transfer`, `total_collected_fees`, and strict no-overdraft enforcement.
- [x] **Task 4.2**: Update `design.md` in-place with reversal state transitions (`AWAITING_CLEARING -> REVERSED` and `SETTLED -> REVERSED`) and fee aggregation rules.
- [x] **Task 4.3**: Implement `reverse_transfer(tx_id)` and `total_collected_fees(currency='USD')` in `ledger_flow.py`.
- [x] **Task 4.4**: Add M4 unit tests in `test_ledger_flow.py` covering reversals from both states, insufficient recipient funds, double-reversal rejection, and fee totals by currency.
