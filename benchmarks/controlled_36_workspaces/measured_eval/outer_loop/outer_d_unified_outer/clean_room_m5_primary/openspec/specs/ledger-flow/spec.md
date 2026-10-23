# Canonical Living Specification — `ledger-flow` (Current State: Milestone 4)

## Overview
`LedgerFlow` is a deterministic, integer-cent settlement ledger supporting multi-currency account creation (`USD`, `EUR`, `GBP`), balance retrieval, replay-safe idempotent same-currency transfers with strict no-overdraft enforcement and tiered platform fees (`100 bps` below `100,000` cents, `50 bps` at or above `100,000` cents, `10`-cent minimum fee floor), high-value clearing holds (`'AWAITING_CLEARING'` for `amount_cents >= 100000`), explicit transfer clearing (`clear_transfer` and backward-compatible alias `settle_pending`), atomic transfer reversals (`reverse_transfer`) with full fee refund, per-currency collected fee reporting (`total_collected_fees`), and chronological account statements (`account_statement`).

## Active Requirements

### Requirement: Account Opening (`open_account`)
The `LedgerFlow` engine SHALL allow opening new currency-denominated accounts with integer cent balances via `open_account(account_id: str, currency: str = 'USD', initial_cents: int = 0) -> dict`.
- `account_id` MUST be a non-empty string after trimming leading/trailing whitespace (`account_id.strip()`), and MUST NOT duplicate an existing account ID.
- `currency` MUST be an uppercase 3-letter ISO currency code in `{'USD', 'EUR', 'GBP'}`.
- `initial_cents` MUST be an integer `>= 0` (rejecting booleans and negative integers).
- Invalid inputs or duplicate `account_id` values MUST raise `ValueError`.

### Requirement: Balance Retrieval (`get_balance`)
The `LedgerFlow` engine SHALL return the current integer balance in cents for an existing account via `get_balance(account_id: str) -> int`.
- Unknown `account_id` values MUST raise `KeyError`.

### Requirement: Transfer Posting (`post_transfer`) with Strict No-Overdraft, Tiered Fee Schedule, 10-Cent Minimum Floor, Inclusive 100,000-Cent Clearing Threshold, and Replay-Safe Idempotency
The `LedgerFlow` engine SHALL execute transfers between two distinct existing accounts of the same currency via `post_transfer(tx_id: str, from_acct: str, to_acct: str, amount_cents: int, timestamp: int) -> dict`.
- **Replay-Safe Idempotency**:
  - If `tx_id` already exists with identical `(from_acct, to_acct, amount_cents)`, `post_transfer` SHALL return a copy of the existing transfer dictionary without debiting or crediting again.
  - If `tx_id` already exists with different `(from_acct, to_acct, amount_cents)`, `post_transfer` SHALL raise `ValueError('Conflicting tx_id')`.
- **Validation & Constitutional No-Overdraft Rule**:
  - Unknown `from_acct` or `to_acct` MUST raise `KeyError`.
  - Empty `tx_id`, same-account transfers (`from_acct == to_acct`), `amount_cents <= 0`, currency mismatch between `from_acct` and `to_acct`, or insufficient funds (`balance < amount_cents + fee_cents`) MUST raise `ValueError`. Overdrafts on `post_transfer` are strictly prohibited.
- **Tiered Fee Schedule**:
  - If `amount_cents >= 100000`: `fee_cents = max(10, (amount_cents * 50) // 10000)` (50 bps = 0.5%).
  - If `amount_cents < 100000`: `fee_cents = max(10, amount_cents // 100)` (100 bps = 1.0%, minimum 10 cents).
- **Immediate Sender Debit & Status Assignment**:
  - `amount_cents + fee_cents` SHALL be debited immediately from `from_acct`.
  - If `amount_cents >= 100000`, the transfer `status` SHALL be set to `'AWAITING_CLEARING'` and `to_acct` SHALL NOT be credited until cleared via `clear_transfer(tx_id)`.
  - If `amount_cents < 100000`, the transfer `status` SHALL be set to `'SETTLED'` and `amount_cents` SHALL be credited to `to_acct` immediately.

### Requirement: High-Value Transfer Clearing (`clear_transfer` & `settle_pending` Alias)
The `LedgerFlow` engine SHALL allow clearing a held `'AWAITING_CLEARING'` transfer via `clear_transfer(tx_id: str) -> dict` (and backward-compatible alias `settle_pending(tx_id: str) -> dict`).
- Unknown `tx_id` values MUST raise `KeyError`.
- Calling `clear_transfer` (or `settle_pending`) on a transfer whose `status` is not currently `'AWAITING_CLEARING'` (e.g., `'SETTLED'` or `'REVERSED'`) MUST raise `ValueError`.
- When valid, the transfer `status` SHALL transition from `'AWAITING_CLEARING'` to `'SETTLED'`, `amount_cents` SHALL be credited to `to_acct`, and a copy of the updated transfer dictionary SHALL be returned.

### Requirement: Transfer Reversal (`reverse_transfer`)
The `LedgerFlow` engine SHALL allow reversing a transfer via `reverse_transfer(tx_id: str) -> dict`.
- Unknown `tx_id` values MUST raise `KeyError`.
- Calling `reverse_transfer` on a transfer that is already `'REVERSED'` MUST raise `ValueError`.
- If the transfer was `'AWAITING_CLEARING'`, `reverse_transfer` SHALL refund `amount_cents + fee_cents` back to `from_acct` and set `status = 'REVERSED'`.
- If the transfer was `'SETTLED'`, `reverse_transfer` SHALL raise `ValueError('Recipient has insufficient funds to reverse')` without mutating state if `to_acct` balance `< amount_cents`; otherwise it SHALL debit `amount_cents` from `to_acct`, refund `amount_cents + fee_cents` back to `from_acct`, and set `status = 'REVERSED'`.

### Requirement: Currency-Scoped Collected Fee Aggregation (`total_collected_fees`)
The `LedgerFlow` engine SHALL return the integer sum of `fee_cents` across all non-reversed (`'SETTLED'` or `'AWAITING_CLEARING'`) transfers in the specified `currency` via `total_collected_fees(currency: str = 'USD') -> int`.
- Invalid `currency` values not in `{'USD', 'EUR', 'GBP'}` MUST raise `ValueError`.

### Requirement: Chronological Account Statement (`account_statement`)
The `LedgerFlow` engine SHALL provide per-account transaction history via `account_statement(account_id: str) -> list[dict]`.
- Unknown `account_id` values MUST raise `KeyError`.
- For an existing account, `account_statement` SHALL return defensive copies (`dict`) of all transfers where `from_acct == account_id` or `to_acct == account_id`, sorted ascending by `(timestamp, insertion_index)`.
