# Feature Specification: 004 — Milestone 4 (Reversals & Constitutional Scope Governance)

## 1. Overview
Extend `LedgerFlow` to support full transfer reversals (`reverse_transfer`), per-currency platform fee aggregation (`total_collected_fees`), and strict non-overdraft invariant enforcement.

## 2. Functional Requirements

### 2.1 Transfer Reversal (`reverse_transfer`)
- **Signature**: `reverse_transfer(tx_id: str) -> dict`
- **Validation**:
  - `tx_id` (trimmed if `str`): Must exist in `self.transactions`; otherwise raise `KeyError`.
  - If the transfer is already in `'REVERSED'` state, raise `ValueError`.
- **Reversal Semantics**:
  - **From `'AWAITING_CLEARING'`**:
    - Refund `amount_cents + fee_cents` to `from_acct`.
    - Do not debit `to_acct` (as `to_acct` was never credited).
    - Set `status = 'REVERSED'` and return a copy of the updated transfer dict.
  - **From `'SETTLED'`**:
    - Verify `to_acct` has `balance >= amount_cents`. If `to_acct` balance `< amount_cents`, raise `ValueError('Recipient has insufficient funds to reverse')` without mutating any state.
    - Debit `amount_cents` from `to_acct`.
    - Refund `amount_cents + fee_cents` to `from_acct`.
    - Set `status = 'REVERSED'` and return a copy of the updated transfer dict.

### 2.2 Total Collected Fees (`total_collected_fees`)
- **Signature**: `total_collected_fees(currency: str = 'USD') -> int`
- **Validation**:
  - Validate `currency` is in `{'USD', 'EUR', 'GBP'}` (raise `ValueError` otherwise).
- **Behavior**:
  - Returns the integer sum of `fee_cents` across all transfers in `currency` whose `status` is `'SETTLED'` or `'AWAITING_CLEARING'` (excluding `'REVERSED'` transfers).

### 2.3 Strict Non-Overdraft Invariant
- Overdrafts on `post_transfer` remain strictly prohibited (`from_acct` balance `< amount_cents + fee_cents` raises `ValueError`).
- Clearing a `'REVERSED'` transfer via `clear_transfer` / `settle_pending` raises `ValueError`.
