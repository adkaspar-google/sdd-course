# Implementation Plan: 001 — Milestone 1 (Greenfield Core Ledger)

## 1. Architecture & Data Structures
- `LedgerFlow`:
  - `SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}`
  - `PENDING_THRESHOLD_CENTS = 100_000`
  - `self.accounts: Dict[str, int]`: Maps `account_id -> balance_cents`.
  - `self.account_records: Dict[str, Dict[str, Any]]`: Maps `account_id -> {"account_id": str, "currency": str, "balance": int, "balance_cents": int, "initial_cents": int}`.
  - `self.entries: List[Dict[str, Any]]`: Ordered list of transaction records.
  - `self.transactions: Dict[str, Dict[str, Any]]`: Maps `tx_id -> transaction record`.

## 2. Implementation Tasks
1. **Task 1: Implement `open_account`**
   - Validate `account_id` is `str` and non-empty after `.strip()`.
   - Check `account_id` is not already in `self.accounts`.
   - Validate `currency` is `str` and in `{"USD", "EUR", "GBP"}`.
   - Validate `initial_cents` is `int` (not `bool`) and `>= 0`.
   - Store balance and account metadata; return account dictionary.
2. **Task 2: Implement `get_balance`**
   - Normalize `account_id` via `.strip()` if `str`.
   - Raise `KeyError` if not found; return integer balance in cents.
3. **Task 3: Implement `post_transfer`**
   - Validate `tx_id` (non-empty trimmed `str`, not duplicate), `amount_cents` (`int > 0`), `timestamp` (`int`).
   - Validate `from_acct` and `to_acct` exist (`KeyError` if unknown) and `from_acct != to_acct` (`ValueError` if identical).
   - Check currency equality between `from_acct` and `to_acct` (`ValueError` on mismatch).
   - Compute `fee_cents = amount_cents // 100` and verify `self.accounts[from_acct] >= amount_cents + fee_cents` (`ValueError` on insufficient funds).
   - Debit `from_acct` by `amount_cents + fee_cents`.
   - If `amount_cents > 100000`, set `status = "PENDING"`; else set `status = "SETTLED"` and credit `to_acct` by `amount_cents`.
   - Record transaction in `self.entries` and `self.transactions[tx_id]` and return it.
4. **Task 4: Unit Testing (`test_ledger_flow.py`)**
   - Test valid account creation, trimming, currencies, and initial balances.
   - Test invalid `open_account` inputs (`ValueError`).
   - Test `get_balance` for existing and unknown accounts (`KeyError`).
   - Test `post_transfer` for settled (`<= 100000`) and pending (`> 100000`) transfers, boundary at `100000` and `100001`, fee calculation, and all error conditions (`KeyError`, `ValueError`).
