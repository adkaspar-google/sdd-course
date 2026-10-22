# LedgerFlow — EARS Requirements Specification (Milestone 4 In-Place State)

## 1. Account Management (`open_account` & `get_balance`)

- **REQ-M1-001**: WHEN `open_account(account_id, currency, initial_cents)` is invoked with a non-empty string `account_id` (after trimming whitespace), a valid 3-letter `currency` in `{'USD', 'EUR', 'GBP'}` (normalized to uppercase), and an integer `initial_cents >= 0`, THE SYSTEM SHALL create a new account with the trimmed `account_id`, uppercase `currency`, and starting balance `initial_cents`, and return the account dictionary.
- **REQ-M1-002**: WHEN `open_account` is invoked with an empty or whitespace-only `account_id`, a duplicate `account_id`, an unsupported `currency` not in `{'USD', 'EUR', 'GBP'}`, or `initial_cents < 0`, THE SYSTEM SHALL raise a `ValueError` without modifying ledger state.
- **REQ-M1-003**: WHEN `get_balance(account_id)` is invoked with an existing `account_id`, THE SYSTEM SHALL return the current integer balance in cents for that account.
- **REQ-M1-004**: WHEN `get_balance(account_id)` is invoked with an unknown `account_id`, THE SYSTEM SHALL raise a `KeyError`.

## 2. Transfer Processing, Tiered Fees & Idempotency (`post_transfer`)

- **REQ-M3-001 (ADDED — Replay-Safe Idempotency)**: WHEN `post_transfer(tx_id, from_acct, to_acct, amount_cents, timestamp)` is invoked with a `tx_id` that already exists and has identical `(from_acct, to_acct, amount_cents)`, THE SYSTEM SHALL return a copy of the existing transfer dictionary without debiting or crediting any account again.
- **REQ-M3-002 (ADDED — Conflicting Replay Detection)**: WHEN `post_transfer(tx_id, from_acct, to_acct, amount_cents, timestamp)` is invoked with a `tx_id` that already exists but has different `(from_acct, to_acct, amount_cents)`, THE SYSTEM SHALL raise `ValueError('Conflicting tx_id')` without modifying ledger state.
- **REQ-M1-005**: WHEN `post_transfer(tx_id, from_acct, to_acct, amount_cents, timestamp)` is invoked with a new `tx_id` and either `from_acct` or `to_acct` does not exist, THE SYSTEM SHALL raise a `KeyError` without modifying any account balances.
- **REQ-M1-006 (MODIFIED — Constitutional No-Overdraft Invariant)**: WHEN `post_transfer` is invoked with an empty `tx_id`, `from_acct == to_acct`, `amount_cents <= 0`, accounts with different currencies, or `from_acct` balance less than `amount_cents + fee_cents`, THE SYSTEM SHALL strictly prohibit overdrafts and raise a `ValueError` without modifying any account balances.
- **REQ-M1-007 (MODIFIED — Tiered Fee & `< 100000` Immediate Settlement)**: WHEN `post_transfer` is invoked with valid parameters for a new `tx_id` and `amount_cents < 100000`, THE SYSTEM SHALL compute `fee_cents = max(10, amount_cents // 100)` (100 bps with a 10-cent minimum floor), immediately debit `amount_cents + fee_cents` from `from_acct`, immediately credit `amount_cents` to `to_acct`, set `status = 'SETTLED'`, record the transaction entry, and return a copy of the transaction dictionary.
- **REQ-M1-008 (RENAMED & MODIFIED — Tiered Fee & `>= 100000` Awaiting Clearing)**: WHEN `post_transfer` is invoked with valid parameters for a new `tx_id` and `amount_cents >= 100000`, THE SYSTEM SHALL compute `fee_cents = max(10, (amount_cents * 50) // 10000)` (50 bps with a 10-cent minimum floor), immediately debit `amount_cents + fee_cents` from `from_acct`, withhold crediting `to_acct`, set `status = 'AWAITING_CLEARING'`, record the transaction entry, and return a copy of the transaction dictionary.

## 3. Clearing & Account Statements (`clear_transfer`, `settle_pending` & `account_statement`)

- **REQ-M2-001 (RENAMED)**: WHEN `clear_transfer(tx_id)` (or its backward-compatible alias `settle_pending(tx_id)`) is invoked for an existing transfer currently in `'AWAITING_CLEARING'` status, THE SYSTEM SHALL transition the transfer's `status` to `'SETTLED'`, credit `amount_cents` to `to_acct`, and return a copy of the updated transfer dictionary.
- **REQ-M2-002 (MODIFIED)**: WHEN `clear_transfer(tx_id)` (or `settle_pending(tx_id)`) is invoked with an unknown `tx_id`, THE SYSTEM SHALL raise a `KeyError`.
- **REQ-M2-003 (MODIFIED)**: WHEN `clear_transfer(tx_id)` (or `settle_pending(tx_id)`) is invoked for an existing transfer whose `status` is not `'AWAITING_CLEARING'`, THE SYSTEM SHALL raise a `ValueError` without modifying any account balances.
- **REQ-M2-004**: WHEN `account_statement(account_id)` is invoked for an existing `account_id`, THE SYSTEM SHALL return copies of all transfer dictionaries where `from_acct == account_id` or `to_acct == account_id`, ordered by `(timestamp, insertion_index)` ascending.
- **REQ-M2-005**: WHEN `account_statement(account_id)` is invoked for an unknown `account_id`, THE SYSTEM SHALL raise a `KeyError`.

## 4. Reversals & Fee Revenue Accounting (`reverse_transfer` & `total_collected_fees`)

- **REQ-M4-001**: WHEN `reverse_transfer(tx_id)` is invoked with an unknown `tx_id`, THE SYSTEM SHALL raise a `KeyError`.
- **REQ-M4-002**: WHEN `reverse_transfer(tx_id)` is invoked for a transfer already in `'REVERSED'` status, THE SYSTEM SHALL raise a `ValueError` without modifying any account balances.
- **REQ-M4-003**: WHEN `reverse_transfer(tx_id)` is invoked for a transfer in `'AWAITING_CLEARING'` status, THE SYSTEM SHALL refund `amount_cents + fee_cents` to `from_acct`, transition `status` to `'REVERSED'`, and return a copy of the updated transfer dictionary.
- **REQ-M4-004**: WHEN `reverse_transfer(tx_id)` is invoked for a transfer in `'SETTLED'` status and `to_acct` has balance `>= amount_cents`, THE SYSTEM SHALL debit `amount_cents` from `to_acct`, refund `amount_cents + fee_cents` to `from_acct`, transition `status` to `'REVERSED'`, and return a copy of the updated transfer dictionary.
- **REQ-M4-005**: WHEN `reverse_transfer(tx_id)` is invoked for a transfer in `'SETTLED'` status and `to_acct` has balance `< amount_cents`, THE SYSTEM SHALL raise `ValueError('Recipient has insufficient funds to reverse')` without mutating any account balances or transfer status.
- **REQ-M4-006**: WHEN `total_collected_fees(currency)` is invoked for a valid currency, THE SYSTEM SHALL return the integer sum of `fee_cents` across all non-reversed (`'SETTLED'` or `'AWAITING_CLEARING'`) transfers in that `currency`.
