# OpenSpec Delta — Milestone 1 (M1: Greenfield Core Ledger)

## ADDED Requirements

### Requirement: Account Opening (`open_account`)
The `LedgerFlow` engine SHALL allow opening new currency-denominated accounts with integer cent balances via `open_account(account_id: str, currency: str = 'USD', initial_cents: int = 0) -> dict`.
- `account_id` MUST be a non-empty string after trimming leading/trailing whitespace (`account_id.strip()`), and MUST NOT duplicate an existing account ID.
- `currency` MUST be an uppercase 3-letter ISO currency code in `{'USD', 'EUR', 'GBP'}`.
- `initial_cents` MUST be an integer `>= 0` (rejecting booleans and negative integers).
- Invalid inputs or duplicate `account_id` values MUST raise `ValueError`.

#### Scenario: Open valid account
- **WHEN** `open_account("acct_1", "USD", 250000)` is called
- **THEN** an account `"acct_1"` is created with currency `"USD"` and balance `250000` cents, returning the account dictionary.

#### Scenario: Reject invalid account parameters or duplicate ID
- **WHEN** `open_account("", "USD", 0)`, `open_account("acct_1", "JPY", 0)`, `open_account("acct_1", "USD", -1)`, or a duplicate `open_account("acct_1", "USD", 100)` is called
- **THEN** `ValueError` is raised and state remains unchanged.

### Requirement: Balance Retrieval (`get_balance`)
The `LedgerFlow` engine SHALL return the current integer balance in cents for an existing account via `get_balance(account_id: str) -> int`.
- Unknown `account_id` values MUST raise `KeyError`.

#### Scenario: Retrieve existing and unknown balances
- **WHEN** `get_balance("acct_1")` is called for an existing account
- **THEN** it returns the integer cent balance; calling `get_balance("unknown")` raises `KeyError`.

### Requirement: Transfer Posting (`post_transfer`) with Flat 1% Fee and High-Value Hold Threshold
The `LedgerFlow` engine SHALL execute transfers between two distinct existing accounts of the same currency via `post_transfer(tx_id: str, from_acct: str, to_acct: str, amount_cents: int, timestamp: int) -> dict`.
- Unknown `from_acct` or `to_acct` MUST raise `KeyError`.
- Same-account transfers (`from_acct == to_acct`), `amount_cents <= 0`, currency mismatch between `from_acct` and `to_acct`, duplicate/empty `tx_id`, or insufficient funds (`balance < amount_cents + fee_cents`) MUST raise `ValueError`.
- A flat `1%` platform fee (`fee_cents = amount_cents // 100`) SHALL be computed and debited immediately from `from_acct` alongside `amount_cents` (`total_debit = amount_cents + fee_cents`).
- If `amount_cents > 100000`, the transfer `status` SHALL be set to `'PENDING'` and `to_acct` SHALL NOT be credited yet.
- If `amount_cents <= 100000`, the transfer `status` SHALL be set to `'SETTLED'` and `amount_cents` SHALL be credited to `to_acct` immediately.

#### Scenario: Immediate settlement for transfer <= 100,000 cents
- **WHEN** `post_transfer("tx_1", "alice", "bob", 50000, 1700000000)` is called where both accounts are `'USD'` and `"alice"` has `100000` cents
- **THEN** `fee_cents` is `500`, `"alice"` is debited `50500` cents (new balance `49500`), `"bob"` is credited `50000` cents immediately, and the returned transaction has `status == 'SETTLED'`.

#### Scenario: Pending hold for high-value transfer > 100,000 cents
- **WHEN** `post_transfer("tx_2", "alice", "bob", 150000, 1700000010)` is called where `"alice"` has `200000` cents
- **THEN** `fee_cents` is `1500`, `"alice"` is debited `151500` cents immediately (new balance `48500`), `"bob"` is NOT credited yet, and the returned transaction has `status == 'PENDING'`.

## MODIFIED Requirements
_None in Milestone 1 (Greenfield baseline)._

## REMOVED Requirements
_None in Milestone 1 (Greenfield baseline)._

## RENAMED Requirements
_None in Milestone 1 (Greenfield baseline)._
