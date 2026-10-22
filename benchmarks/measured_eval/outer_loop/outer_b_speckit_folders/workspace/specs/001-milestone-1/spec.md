# Feature Specification: 001 — Milestone 1 (Greenfield Core Ledger)

## 1. Overview
Implement the core `LedgerFlow` multi-currency account and transfer settlement engine supporting account creation, balance retrieval, and same-currency transfers with flat platform fees and high-value pending holds.

## 2. Functional Requirements

### 2.1 Account Creation (`open_account`)
- **Signature**: `open_account(account_id: str, currency: str = 'USD', initial_cents: int = 0) -> dict`
- **Validation**:
  - `account_id`: Must be a `str`, trimmed of leading/trailing whitespace, non-empty, and unique across existing accounts.
  - `currency`: Must be an uppercase 3-letter currency code in `{'USD', 'EUR', 'GBP'}`.
  - `initial_cents`: Must be an integer (`not isinstance(initial_cents, bool)`) with `initial_cents >= 0`.
  - Raise `ValueError` on any invalid input or duplicate `account_id`.
- **Return Value**: Dictionary containing account details (`account_id`, `currency`, `balance`, `balance_cents`).

### 2.2 Balance Inquiry (`get_balance`)
- **Signature**: `get_balance(account_id: str) -> int`
- **Behavior**:
  - Returns the current integer balance in cents for `account_id` (trimmed).
  - Raises `KeyError` if `account_id` does not exist.

### 2.3 Transfer Posting (`post_transfer`)
- **Signature**: `post_transfer(tx_id: str, from_acct: str, to_acct: str, amount_cents: int, timestamp: int) -> dict`
- **Validation**:
  - `tx_id`: Non-empty trimmed string, unique across posted transfers (raise `ValueError` if invalid or duplicate).
  - `from_acct`, `to_acct`: Must exist in the ledger (raise `KeyError` if either account is unknown).
  - Distinct accounts: `from_acct != to_acct` (raise `ValueError` if same account).
  - `amount_cents`: Integer `> 0` (raise `ValueError` if `<= 0` or non-int).
  - Currency match: `from_acct` and `to_acct` must have identical currency codes (raise `ValueError` on mismatch).
  - Fee & funds check: Platform fee is `fee_cents = amount_cents // 100` (flat `1%`). `from_acct` must have `balance >= amount_cents + fee_cents` (raise `ValueError` on insufficient funds).
- **Execution & Settlement Status**:
  - Immediately debit `amount_cents + fee_cents` from `from_acct`.
  - If `amount_cents > 100000`: set `status = 'PENDING'` and do **not** credit `to_acct` yet.
  - Otherwise (`amount_cents <= 100000`): set `status = 'SETTLED'` and credit `amount_cents` to `to_acct` immediately.
- **Return Value**: Transaction entry dictionary (`tx_id`, `from_acct`, `to_acct`, `amount_cents`, `fee_cents`, `currency`, `timestamp`, `status`).

## 3. Acceptance Criteria
- Accounts can be opened in `USD`, `EUR`, and `GBP` with zero or positive initial cents.
- Invalid account IDs, unsupported/lowercase currencies, negative initial balances, and duplicate account IDs raise `ValueError`.
- Unknown accounts in `get_balance` and `post_transfer` raise `KeyError`.
- Transfers `<= 100000` cents settle immediately (`status == 'SETTLED'`), debiting `amount_cents + (amount_cents // 100)` from sender and crediting `amount_cents` to receiver.
- Transfers `> 100000` cents remain pending (`status == 'PENDING'`), debiting `amount_cents + (amount_cents // 100)` from sender without crediting receiver.
