# Feature Specification: 003 — Milestone 3 (Requirement Rename & Tiered Fee Mutation)

## 1. Overview
Evolve `LedgerFlow` to rename the high-value hold state and clearing method, mutate the clearing threshold and fee schedule to a tiered model with a 10-cent floor, and add replay-safe idempotency to `post_transfer`.

## 2. Requirement Changes

### 2.1 Status & Method Rename (`RENAMED`)
- **Status Rename**: High-value hold status is renamed from `'PENDING'` to `'AWAITING_CLEARING'` across all new transfers and clearing state checks.
- **Method Rename**: `settle_pending(tx_id: str) -> dict` is renamed to `clear_transfer(tx_id: str) -> dict`.
  - Transitions a transfer in `'AWAITING_CLEARING'` state to `'SETTLED'` and credits `amount_cents` to `to_acct`.
  - Raises `KeyError` if `tx_id` is unknown, or `ValueError` if the transfer status is not `'AWAITING_CLEARING'`.
  - `settle_pending(tx_id: str) -> dict` is retained as a backward-compatible alias delegating to `clear_transfer(tx_id)`.

### 2.2 Threshold & Tiered Fee Mutation (`MODIFIED`)
- **Clearing Threshold**: Now inclusive at `amount_cents >= 100000`:
  - `amount_cents >= 100000`: initial `status = 'AWAITING_CLEARING'` (`to_acct` not credited until cleared).
  - `amount_cents < 100000`: initial `status = 'SETTLED'` (`to_acct` credited immediately).
- **Tiered Platform Fee with 10-Cent Minimum Floor**:
  - If `amount_cents >= 100000`: `fee_cents = max(10, (amount_cents * 50) // 10000)` (50 bps = 0.5%).
  - If `amount_cents < 100000`: `fee_cents = max(10, amount_cents // 100)` (100 bps = 1.0%, minimum 10 cents).

### 2.3 Replay-Safe Idempotency (`ADDED`)
- When `post_transfer` is called with an existing `tx_id`:
  - If `(from_acct, to_acct, amount_cents)` matches the existing transfer record, return a shallow copy of the existing transfer dictionary without re-debiting or re-crediting balances or appending a duplicate entry.
  - If any of `(from_acct, to_acct, amount_cents)` differs from the existing transfer record, raise `ValueError('Conflicting tx_id')`.
