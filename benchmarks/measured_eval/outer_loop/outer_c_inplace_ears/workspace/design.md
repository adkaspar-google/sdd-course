# LedgerFlow — Technical Design (Milestone 4 In-Place State)

## 1. Architecture Overview
`LedgerFlow` implements an in-memory transactional settlement ledger supporting multi-currency accounts (`USD`, `EUR`, `GBP`), replay-safe idempotency on `tx_id`, tiered platform fee calculation with a 10-cent minimum floor, threshold-driven clearing states (`SETTLED` for `< 100000` vs. `AWAITING_CLEARING` for `>= 100000`), explicit clearing (`clear_transfer` and backward-compatible alias `settle_pending`), transfer reversals (`reverse_transfer`), currency-scoped fee revenue aggregation (`total_collected_fees`), and deterministic chronological account statements (`account_statement`).

## 2. Data Structures

### 2.1 Account State
- `self._accounts: Dict[str, Dict[str, Any]]`: Canonical account metadata and balance store keyed by trimmed `account_id`:
  - `account_id` (`str`): Trimmed non-empty account identifier.
  - `currency` (`str`): Uppercase 3-letter ISO currency code (`'USD'`, `'EUR'`, `'GBP'`).
  - `balance` (`int`): Current integer balance in cents (strictly non-negative; overdrafts are prohibited).
  - `balance_cents` (`int`): Kept synchronized with `balance` for caller compatibility.
- `self.accounts: Dict[str, int]`: Maps `account_id -> balance` in cents, synchronized on every balance mutation.

### 2.2 Transaction Entries & State Machine
- `self.entries: List[Dict[str, Any]]`: Insertion-ordered log of transfer dictionaries. Position in `self.entries` serves as `insertion_index` for deterministic tie-breaking on equal timestamps.
- `self._tx_index: Dict[str, Dict[str, Any]]`: Maps trimmed `tx_id -> transfer dict` to support O(1) replay-safe idempotency checks, clearing, and reversals.
- Transfer lifecycle states:
  - `'AWAITING_CLEARING'` -> `'SETTLED'` (via `clear_transfer` / `settle_pending`)
  - `'AWAITING_CLEARING'` -> `'REVERSED'` (via `reverse_transfer`; refunds `amount_cents + fee_cents` to `from_acct`)
  - `'SETTLED'` -> `'REVERSED'` (via `reverse_transfer`; debits `amount_cents` from `to_acct` if sufficient balance, refunds `amount_cents + fee_cents` to `from_acct`)

## 3. Fee Schedule & Clearing Threshold (M3–M4)

- **Clearing Threshold**: `CLEARING_THRESHOLD_CENTS = 100000` (inclusive).
  - `amount_cents >= 100000`: Initial status is `'AWAITING_CLEARING'`.
  - `amount_cents < 100000`: Initial status is `'SETTLED'`.
- **Tiered Fee Schedule**:
  - High-value tier (`amount_cents >= 100000`): `fee_cents = max(10, (amount_cents * 50) // 10000)` (50 bps = 0.5%).
  - Standard tier (`amount_cents < 100000`): `fee_cents = max(10, amount_cents // 100)` (100 bps = 1.0%, 10-cent floor).

## 4. Core Methods & Validation Flows

1. **`open_account(account_id: str, currency: str = 'USD', initial_cents: int = 0) -> dict`**
   - Trims `account_id`; raises `ValueError` if empty or already present in `self._accounts`.
   - Normalizes `currency` via `.strip().upper()`; raises `ValueError` if not in `{'USD', 'EUR', 'GBP'}`.
   - Validates `initial_cents` is a non-boolean integer `>= 0`; raises `ValueError` otherwise.
   - Stores and returns a copy of the account dictionary.

2. **`get_balance(account_id: str) -> int`**
   - Resolves `account_id` (trimmed) in `self._accounts`; raises `KeyError` if unknown.
   - Returns integer balance in cents.

3. **`post_transfer(tx_id: str, from_acct: str, to_acct: str, amount_cents: int, timestamp: int) -> dict`**
   - Validates `tx_id` is a non-empty string (after trimming).
   - **Idempotency Gate**: If `cleaned_tx_id in self._tx_index`:
     - Compares normalized `(from_acct, to_acct, amount_cents)` against the stored entry.
     - If identical, returns `dict(existing_entry)` without mutating state.
     - If any parameter differs, raises `ValueError('Conflicting tx_id')`.
   - Validates `amount_cents` (`> 0` int) and `timestamp` (int).
   - Resolves `from_acct` and `to_acct` in `self._accounts`; raises `KeyError` if either account does not exist.
   - Raises `ValueError` if `from_acct == to_acct` or account currencies differ.
   - Computes tiered `fee_cents` and `total_debit = amount_cents + fee_cents`.
   - Strictly enforces no-overdraft rule: raises `ValueError` if `from_acct` balance `< total_debit`.
   - Debits `total_debit` from `from_acct`.
   - If `amount_cents >= 100000`, sets `status = 'AWAITING_CLEARING'` without crediting `to_acct`; otherwise sets `status = 'SETTLED'` and credits `amount_cents` to `to_acct` immediately.

4. **`clear_transfer(tx_id: str) -> dict` & `settle_pending(tx_id: str) -> dict`**
   - Resolves `tx_id` in `self._tx_index`; raises `KeyError` if unknown.
   - Verifies `entry['status'] == 'AWAITING_CLEARING'`; raises `ValueError` otherwise.
   - Transitions `entry['status'] = 'SETTLED'`, credits `entry['amount_cents']` to `entry['to_acct']`, and returns `dict(entry)`.
   - `settle_pending(tx_id)` delegates directly to `clear_transfer(tx_id)`.

5. **`reverse_transfer(tx_id: str) -> dict`**
   - Resolves `tx_id` in `self._tx_index`; raises `KeyError` if unknown.
   - If `entry['status'] == 'REVERSED'`, raises `ValueError`.
   - If `entry['status'] == 'AWAITING_CLEARING'`:
     - Refunds `amount_cents + fee_cents` to `from_acct` and sets `entry['status'] = 'REVERSED'`.
   - If `entry['status'] == 'SETTLED'`:
     - Checks `to_acct` balance `>= amount_cents`; if not, raises `ValueError('Recipient has insufficient funds to reverse')` without mutating state.
     - Debits `amount_cents` from `to_acct`, refunds `amount_cents + fee_cents` to `from_acct`, and sets `entry['status'] = 'REVERSED'`.
   - Returns `dict(entry)`.

6. **`total_collected_fees(currency: str = 'USD') -> int`**
   - Normalizes `currency` via `.strip().upper()` and validates against `SUPPORTED_CURRENCIES` (`ValueError` if invalid).
   - Sums `entry['fee_cents']` across all entries in `self.entries` where `entry['currency'] == cleaned_currency` and `entry['status'] in ('SETTLED', 'AWAITING_CLEARING')`.

7. **`account_statement(account_id: str) -> list[dict]`**
   - Resolves `account_id` in `self._accounts`; raises `KeyError` if unknown.
   - Filters `enumerate(self.entries)` for transfers where `from_acct == resolved_id` or `to_acct == resolved_id`.
   - Sorts matching entries by `(entry['timestamp'], insertion_index)` ascending and returns shallow copies `[dict(e) for _, e in matches]`.
