# Implementation Plan: 003 — Milestone 3 (Requirement Rename & Tiered Fee Mutation)

## 1. Code Updates in `ledger_flow.py`
1. **Constants & Helpers**:
   - `CLEARING_THRESHOLD_CENTS = 100_000`
   - `_calculate_fee(amount_cents: int) -> int`:
     - If `amount_cents >= 100_000`: `return max(10, (amount_cents * 50) // 10000)`
     - Else: `return max(10, amount_cents // 100)`
2. **`post_transfer` Updates**:
   - Normalize `clean_tx_id`, `src`, and `dst`.
   - Check idempotency if `clean_tx_id in self.transactions`:
     - If `(existing["from_acct"], existing["to_acct"], existing["amount_cents"]) == (src, dst, amount_cents)`, return `dict(existing)`.
     - Otherwise raise `ValueError("Conflicting tx_id")`.
   - Compute `fee_cents = self._calculate_fee(amount_cents)`.
   - Set `status = "AWAITING_CLEARING"` when `amount_cents >= 100_000`, else `"SETTLED"`.
3. **`clear_transfer` & `settle_pending`**:
   - Implement `clear_transfer(tx_id: str) -> Dict[str, Any]` checking `entry["status"] == "AWAITING_CLEARING"`.
   - Keep `settle_pending(tx_id: str) -> Dict[str, Any]` delegating to `self.clear_transfer(tx_id)`.

## 2. Test Updates in `test_ledger_flow.py`
- Update M1/M2 assertions for evolved M3 rules (`AWAITING_CLEARING`, inclusive `100000` boundary, 10-cent minimum fee floor, and 50 bps high-value fee).
- Add `TestLedgerFlowM3` testing:
  - Tiered fees (10-cent floor for small amounts, 100 bps for `< 100000`, 50 bps for `>= 100000`).
  - Inclusive `100000` threshold (`99999` -> `SETTLED`, `100000` -> `AWAITING_CLEARING`).
  - `clear_transfer` and `settle_pending` alias.
  - Replay-safe idempotency (identical parameters return copy without balance side effects; mismatched `from_acct`, `to_acct`, or `amount_cents` raises `ValueError('Conflicting tx_id')`).
