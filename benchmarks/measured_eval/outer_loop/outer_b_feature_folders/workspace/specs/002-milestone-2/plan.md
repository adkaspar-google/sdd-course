# Implementation Plan: 002 — Milestone 2 (Clearing & Account Statements)

## 1. Architecture & State Updates
- `self.entries` already maintains transfers in insertion order, so `enumerate(self.entries)` provides `insertion_index` directly.
- `settle_pending(tx_id: str) -> Dict[str, Any]`:
  - Normalize `tx_id` (`tx_id.strip()` if `isinstance(tx_id, str)`).
  - Lookup in `self.transactions`; if missing, raise `KeyError`.
  - Verify `entry["status"] == "PENDING"`; otherwise raise `ValueError`.
  - Update `entry["status"] = "SETTLED"`.
  - Credit `dst = entry["to_acct"]` with `entry["amount_cents"]` in both `self.accounts[dst]` and `self.account_records[dst]`.
  - Return `dict(entry)`.
- `account_statement(account_id: str) -> List[Dict[str, Any]]`:
  - Normalize `account_id` (`account_id.strip()` if `isinstance(account_id, str)`).
  - Verify `acct_id in self.accounts`; if missing, raise `KeyError`.
  - Collect `(idx, entry)` from `enumerate(self.entries)` where `entry["from_acct"] == acct_id or entry["to_acct"] == acct_id`.
  - Sort by `(entry["timestamp"], idx)` ascending and return `[dict(entry) for _, entry in matches]`.

## 2. Verification Plan
- Add unit tests in `test_ledger_flow.py` (`TestLedgerFlowM2`) covering:
  - Settling a pending transfer updates status and credits destination balance.
  - Settling an unknown `tx_id` raises `KeyError`.
  - Settling an already settled transfer (either initially settled or previously settled via `settle_pending`) raises `ValueError`.
  - `account_statement` on unknown account raises `KeyError`.
  - `account_statement` returns copies sorted by `(timestamp, insertion_index)` ascending and reflects updated status after `settle_pending`.
