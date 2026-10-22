# OpenSpec Delta — Milestone 2 (M2: Clearing & Account Statements)

## ADDED Requirements

### Requirement: Pending Transfer Clearing (`settle_pending`)
The `LedgerFlow` engine SHALL allow settling a held `'PENDING'` transfer via `settle_pending(tx_id: str) -> dict`.
- Unknown `tx_id` values MUST raise `KeyError`.
- Calling `settle_pending` on a transfer whose `status` is not currently `'PENDING'` (e.g., already `'SETTLED'`) MUST raise `ValueError`.
- When valid, the transfer `status` SHALL transition from `'PENDING'` to `'SETTLED'`, `amount_cents` SHALL be credited to `to_acct`, and a copy of the updated transfer dictionary SHALL be returned.

#### Scenario: Settle a pending high-value transfer
- **WHEN** `settle_pending("tx_high")` is called on a `'PENDING'` transfer of `150000` cents to `"bob"`
- **THEN** `"bob"` is credited `150000` cents, the transfer `status` becomes `'SETTLED'`, and re-calling `settle_pending("tx_high")` raises `ValueError`.

### Requirement: Chronological Account Statement (`account_statement`)
The `LedgerFlow` engine SHALL provide per-account transaction history via `account_statement(account_id: str) -> list[dict]`.
- Unknown `account_id` values MUST raise `KeyError`.
- For an existing account, `account_statement` SHALL return defensive copies (`dict`) of all transfers where `from_acct == account_id` or `to_acct == account_id`, sorted ascending by `(timestamp, insertion_index)`.

#### Scenario: Retrieve sorted account statement with defensive copies
- **WHEN** `account_statement("alice")` is called after multiple transfers with out-of-order and tied timestamps
- **THEN** it returns copies of all matching transfers ordered by `(timestamp, insertion_index)` ascending, and mutating the returned list or dictionaries does not alter internal ledger state.

## MODIFIED Requirements

### Requirement: Transfer Entry Lifecycle (`post_transfer` -> `settle_pending`)
High-value transfers (`amount_cents > 100000`) created in `'PENDING'` status by `post_transfer` (which previously remained permanently uncredited in M1) now transition to `'SETTLED'` and credit `amount_cents` to `to_acct` when `settle_pending(tx_id)` is invoked.

## REMOVED Requirements
_None in Milestone 2._

## RENAMED Requirements
_None in Milestone 2._
