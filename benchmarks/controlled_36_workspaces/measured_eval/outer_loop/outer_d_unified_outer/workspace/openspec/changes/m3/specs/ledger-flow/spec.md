# OpenSpec Delta — Milestone 3 (M3: Requirement Rename & Tiered Fee Mutation)

## ADDED Requirements

### Requirement: Replay-Safe Transfer Idempotency (`post_transfer`)
The `LedgerFlow` engine SHALL enforce replay-safe idempotency on `tx_id` in `post_transfer(tx_id, from_acct, to_acct, amount_cents, timestamp) -> dict`.
- If `tx_id` already exists in the ledger with identical `(from_acct, to_acct, amount_cents)`, `post_transfer` SHALL return a defensive copy of the existing transfer dictionary without debiting `from_acct`, crediting `to_acct`, or appending a duplicate entry.
- If `tx_id` already exists in the ledger with different `(from_acct, to_acct, amount_cents)`, `post_transfer` SHALL raise `ValueError('Conflicting tx_id')`.

#### Scenario: Idempotent replay of an existing transfer
- **WHEN** `post_transfer("tx_1", "alice", "bob", 50000, 1700000000)` is called twice with identical `(from_acct, to_acct, amount_cents)`
- **THEN** the second call returns a copy of `"tx_1"` without debiting `"alice"` or crediting `"bob"` a second time.

#### Scenario: Conflicting replay of an existing tx_id
- **WHEN** `post_transfer("tx_1", "alice", "bob", 60000, 1700000005)` is called after `"tx_1"` was already registered with `amount_cents = 50000`
- **THEN** `ValueError('Conflicting tx_id')` is raised and ledger balances remain unchanged.

## MODIFIED Requirements

### Requirement: Transfer Posting (`post_transfer`) with Tiered Fee Schedule, 10-Cent Minimum Floor, and Inclusive 100,000-Cent Clearing Threshold
The `LedgerFlow` engine SHALL compute tiered platform fees and clearing holds in `post_transfer(tx_id: str, from_acct: str, to_acct: str, amount_cents: int, timestamp: int) -> dict`:
- **Tiered Platform Fee with 10-Cent Floor**:
  - If `amount_cents >= 100000`: `fee_cents = max(10, (amount_cents * 50) // 10000)` (50 bps = 0.5%).
  - If `amount_cents < 100000`: `fee_cents = max(10, amount_cents // 100)` (100 bps = 1.0%, minimum 10 cents).
- **Immediate Sender Debit**: `from_acct` MUST have `balance >= amount_cents + fee_cents`, and `amount_cents + fee_cents` SHALL be debited immediately from `from_acct`.
- **Inclusive Clearing Hold Threshold (`amount_cents >= 100000`)**:
  - If `amount_cents >= 100000`, the transfer `status` SHALL be set to `'AWAITING_CLEARING'` and `to_acct` SHALL NOT be credited until cleared via `clear_transfer(tx_id)`.
  - If `amount_cents < 100000`, the transfer `status` SHALL be set to `'SETTLED'` and `amount_cents` SHALL be credited to `to_acct` immediately.

#### Scenario: High-value transfer at inclusive 100,000-cent boundary
- **WHEN** `post_transfer("tx_100k", "alice", "bob", 100000, 1700000000)` is called
- **THEN** `fee_cents` is `500` (50 bps), `"alice"` is debited `100500` cents immediately, `"bob"` is not credited yet, and `status` is `'AWAITING_CLEARING'`.

#### Scenario: Standard transfer below 100,000 cents with 10-cent minimum fee floor
- **WHEN** `post_transfer("tx_small", "alice", "bob", 500, 1700000010)` is called
- **THEN** `fee_cents` is `10` (`max(10, 500 // 100)`), `"alice"` is debited `510` cents, `"bob"` is credited `500` cents immediately, and `status` is `'SETTLED'`.

## REMOVED Requirements

### Requirement: Flat 1% Unfloored Fee and Strict `> 100000` Threshold
- Removed the M1 flat `1%` fee without minimum floor (`amount_cents // 100` yielding `0` fee for `< 100` cents) and replaced it with the M3 tiered fee schedule (`50 bps` for `>= 100000`, `100 bps` for `< 100000`, with a `10`-cent minimum floor).
- Removed the strict `amount_cents > 100000` hold boundary; `amount_cents == 100000` now enters `'AWAITING_CLEARING'`.

## RENAMED Requirements

### Requirement: Status `'PENDING'` Renamed to `'AWAITING_CLEARING'`
- **FROM**: Transfer hold status `'PENDING'`
- **TO**: Transfer hold status `'AWAITING_CLEARING'` across all new transfers and clearing state checks.

### Requirement: Method `settle_pending` Renamed to `clear_transfer` (with Backward-Compatible Alias)
- **FROM**: `settle_pending(tx_id: str) -> dict`
- **TO**: `clear_transfer(tx_id: str) -> dict` (with `settle_pending(tx_id: str) -> dict` retained as a backward-compatible alias delegating directly to `clear_transfer(tx_id)`).
