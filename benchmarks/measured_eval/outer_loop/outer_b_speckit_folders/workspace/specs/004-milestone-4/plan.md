# Implementation Plan: 004 — Milestone 4 (Reversals & Constitutional Scope Governance)

## 1. Code Updates in `ledger_flow.py`
1. **Implement `reverse_transfer(tx_id: str) -> Dict[str, Any]`**:
   - Normalize `clean_tx_id = tx_id.strip() if isinstance(tx_id, str) else tx_id`.
   - Raise `KeyError` if `clean_tx_id not in self.transactions`.
   - Retrieve `entry = self.transactions[clean_tx_id]`.
   - If `entry["status"] == "REVERSED"`, raise `ValueError("Transfer is already REVERSED")`.
   - If `entry["status"] == "AWAITING_CLEARING"`:
     - Refund `entry["amount_cents"] + entry["fee_cents"]` to `entry["from_acct"]`.
     - Set `entry["status"] = "REVERSED"`.
   - Else if `entry["status"] == "SETTLED"`:
     - Check `self.accounts[entry["to_acct"]] < entry["amount_cents"]`; if so, raise `ValueError("Recipient has insufficient funds to reverse")`.
     - Debit `entry["amount_cents"]` from `entry["to_acct"]`.
     - Refund `entry["amount_cents"] + entry["fee_cents"]` to `entry["from_acct"]`.
     - Set `entry["status"] = "REVERSED"`.
   - Sync `self.account_records` balances and return `dict(entry)`.
2. **Implement `total_collected_fees(currency: str = "USD") -> int`**:
   - Validate `currency in self.SUPPORTED_CURRENCIES` (raise `ValueError` if invalid).
   - Sum `entry["fee_cents"]` for `entry in self.entries` where `entry["currency"] == currency` and `entry["status"] in ("SETTLED", "AWAITING_CLEARING")`.

## 2. Verification Plan
- Add `TestLedgerFlowM4` in `test_ledger_flow.py` covering:
  - Reversing an `'AWAITING_CLEARING'` transfer refunds `amount_cents + fee_cents` to sender and leaves recipient balance unchanged.
  - Reversing a `'SETTLED'` transfer debits `amount_cents` from recipient and refunds `amount_cents + fee_cents` to sender.
  - Reversing a `'SETTLED'` transfer when recipient has insufficient funds raises `ValueError('Recipient has insufficient funds to reverse')` with zero state mutation.
  - Reversing an already `'REVERSED'` transfer raises `ValueError`; reversing unknown `tx_id` raises `KeyError`.
  - `total_collected_fees` accurately sums active fees per currency and excludes reversed transfers.
