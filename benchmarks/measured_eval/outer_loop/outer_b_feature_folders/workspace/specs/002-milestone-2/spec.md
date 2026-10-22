# Feature Specification: 002 — Milestone 2 (Clearing & Account Statements)

## 1. Overview
Extend `LedgerFlow` with pending transfer clearing (`settle_pending`) and chronological per-account transfer statements (`account_statement`).

## 2. Functional Requirements

### 2.1 Pending Transfer Settlement (`settle_pending`)
- **Signature**: `settle_pending(tx_id: str) -> dict`
- **Validation**:
  - `tx_id` (trimmed if `str`): Must refer to an existing transfer in the ledger. Raise `KeyError` if `tx_id` is unknown.
  - Transfer `status`: Must currently be `'PENDING'`. Raise `ValueError` if `status != 'PENDING'` (e.g., already `'SETTLED'`).
- **Behavior**:
  - Transitions the transfer's `status` from `'PENDING'` to `'SETTLED'`.
  - Credits `amount_cents` to `to_acct`.
  - Returns a copy of the updated transfer dictionary.

### 2.2 Account Statement (`account_statement`)
- **Signature**: `account_statement(account_id: str) -> list[dict]`
- **Validation**:
  - `account_id` (trimmed if `str`): Must exist in the ledger. Raise `KeyError` if `account_id` is unknown.
- **Behavior**:
  - Filters all posted transfers where `from_acct == account_id` or `to_acct == account_id`.
  - Sorts matching transfers by `(timestamp, insertion_index)` ascending.
  - Returns shallow copies (`dict(entry)`) of each matching transfer dictionary so external mutation does not corrupt internal ledger state.

## 3. Acceptance Criteria
- `settle_pending(tx_id)` transitions `'PENDING'` transfers to `'SETTLED'` and credits `to_acct` by `amount_cents`.
- Calling `settle_pending` on an unknown `tx_id` raises `KeyError`.
- Calling `settle_pending` on an already `'SETTLED'` transfer raises `ValueError`.
- `account_statement(account_id)` raises `KeyError` for unknown accounts and returns copies of all transfers involving `account_id` ordered by `(timestamp, insertion_index)` ascending.
