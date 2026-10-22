# OpenSpec Delta — Milestone 4 (M4: Reversals & Constitutional Scope Governance)

## ADDED Requirements

### Requirement: Transfer Reversal (`reverse_transfer`)
The `LedgerFlow` engine SHALL support reversing both `'AWAITING_CLEARING'` and `'SETTLED'` transfers via `reverse_transfer(tx_id: str) -> dict`.
- Unknown `tx_id` values MUST raise `KeyError`.
- Calling `reverse_transfer` on a transfer whose `status` is already `'REVERSED'` MUST raise `ValueError`.
- If the transfer `status` is `'AWAITING_CLEARING'`, `reverse_transfer` SHALL refund `amount_cents + fee_cents` back to `from_acct` (without debiting `to_acct`, which was never credited), set `status = 'REVERSED'`, and return a copy of the updated transfer dictionary.
- If the transfer `status` is `'SETTLED'`, `reverse_transfer` SHALL first verify that `to_acct` has `balance >= amount_cents`; if `to_acct` balance `< amount_cents`, it MUST raise `ValueError('Recipient has insufficient funds to reverse')` without mutating any state. Otherwise, it SHALL debit `amount_cents` from `to_acct`, refund `amount_cents + fee_cents` back to `from_acct`, set `status = 'REVERSED'`, and return a copy of the updated transfer dictionary.

#### Scenario: Reverse an awaiting-clearing transfer
- **WHEN** `reverse_transfer("tx_100k")` is called on an `'AWAITING_CLEARING'` transfer (`amount_cents = 100000`, `fee_cents = 500`)
- **THEN** `from_acct` is refunded `100500` cents, `to_acct` balance is unchanged, and `status` becomes `'REVERSED'`.

#### Scenario: Reverse a settled transfer with sufficient recipient funds
- **WHEN** `reverse_transfer("tx_settled")` is called on a `'SETTLED'` transfer (`amount_cents = 50000`, `fee_cents = 500`) and `to_acct` has at least `50000` cents
- **THEN** `to_acct` is debited `50000` cents, `from_acct` is refunded `50500` cents, and `status` becomes `'REVERSED'`.

#### Scenario: Reject settled reversal when recipient has insufficient funds
- **WHEN** `reverse_transfer("tx_settled")` is called after `to_acct` has spent its funds such that `balance < amount_cents`
- **THEN** `ValueError('Recipient has insufficient funds to reverse')` is raised and all balances and statuses remain unchanged.

### Requirement: Currency-Scoped Collected Fee Aggregation (`total_collected_fees`)
The `LedgerFlow` engine SHALL report collected platform fees via `total_collected_fees(currency: str = 'USD') -> int`.
- `currency` MUST be a valid uppercase 3-letter currency code in `{'USD', 'EUR', 'GBP'}` (raising `ValueError` otherwise).
- Returns the integer sum of `fee_cents` across all non-reversed transfers (`status` in `{'SETTLED', 'AWAITING_CLEARING'}`) denominated in `currency`. Transfers in `'REVERSED'` status SHALL NOT contribute to collected fees.

#### Scenario: Compute collected fees excluding reversed transfers
- **WHEN** two `'USD'` transfers with fees `500` and `200` are posted and the second is reversed via `reverse_transfer`
- **THEN** `total_collected_fees('USD')` returns `500`.

## MODIFIED Requirements

### Requirement: Transfer Lifecycle State Machine (`SETTLED` / `AWAITING_CLEARING` -> `REVERSED`)
- Transfers in `'AWAITING_CLEARING'` or `'SETTLED'` status may now transition to terminal `'REVERSED'` status via `reverse_transfer(tx_id)`.
- Overdrafts on `post_transfer` remain strictly prohibited (`from_acct` balance `< amount_cents + fee_cents` MUST raise `ValueError`).

## REMOVED Requirements
_None in Milestone 4._

## RENAMED Requirements
_None in Milestone 4._
