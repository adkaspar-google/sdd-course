# Conductor Tech Stack & Architectural Constraints — `LedgerFlow`

- **Runtime**: Python 3.11+ standard library only (zero external runtime dependencies).
- **Monetary Representation**: Exact integer cents (`int`, strictly rejecting `float` and `bool`).
- **Supported Currencies**: `'USD'`, `'EUR'`, `'GBP'` (uppercase 3-letter ISO codes).
- **Constitutional No-Overdraft Invariant**: `post_transfer` strictly prohibits overdrafts (`from_acct` balance `< amount_cents + fee_cents` raises `ValueError`); `reverse_transfer` on `'SETTLED'` transfers also prohibits recipient overdrafts (`to_acct` balance `< amount_cents` raises `ValueError('Recipient has insufficient funds to reverse')`).
- **Fee & Clearing Policy (M3–M4 Active)**:
  - `< 100,000` cents: `fee_cents = max(10, amount_cents // 100)` (100 bps, 10c floor), immediate `'SETTLED'`.
  - `>= 100,000` cents: `fee_cents = max(10, (amount_cents * 50) // 10000)` (50 bps, 10c floor), starts in `'AWAITING_CLEARING'`, cleared via `clear_transfer(tx_id)` (alias `settle_pending(tx_id)`).
  - Reversals (`reverse_transfer`) refund `amount_cents + fee_cents` to `from_acct` and exclude `'REVERSED'` transfers from `total_collected_fees(currency)`.
- **Idempotency**: Replay-safe on identical `(tx_id, from_acct, to_acct, amount_cents)`; raises `ValueError('Conflicting tx_id')` on parameter mismatch.
- **Ordering & Immutability**: Account statements sort deterministically by `(timestamp, insertion_index)` ascending and return defensive dictionary copies (`dict(entry)`).
- **Test Harness**: `unittest` (`python3 -m unittest discover -s <workspace>` or `python3 test_ledger_flow.py`).
- **Outer-Loop Architecture**: Arm D Unified Outer-Loop SDD (`Conductor` track plans + `OpenSpec` two-plane delta engine + 8-section `SPEC.md` Single Source of Truth).
