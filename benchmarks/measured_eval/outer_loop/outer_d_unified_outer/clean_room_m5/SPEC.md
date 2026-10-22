# LedgerFlow — Clean-Room Solution Specification (`SPEC.md` SSOT — Milestone 4)

## 1. Domain Intent
`LedgerFlow` is an in-memory, deterministic settlement ledger engine that manages multi-currency accounts (`USD`, `EUR`, `GBP`) and processes atomic, replay-safe integer-cent transfers under strict no-overdraft governance. As of Milestone 4 (M4 — Reversals & Constitutional Scope Governance), the system provides:
- Account creation (`open_account`) and balance inquiry (`get_balance`).
- Replay-safe idempotent same-currency transfer initiation (`post_transfer`) with strict overdraft prohibition (`balance >= amount_cents + fee_cents`) and a tiered platform fee with a `10`-cent minimum floor (`100 bps` for `< 100,000` cents; `50 bps` for `>= 100,000` cents).
- Immediate settlement (`'SETTLED'`) for transfers strictly below `100,000` cents, and clearing hold (`'AWAITING_CLEARING'`) for transfers at or above `100,000` cents (`amount_cents >= 100000`).
- Explicit clearing of held transfers via `clear_transfer(tx_id)` (and backward-compatible alias `settle_pending(tx_id)`).
- Full transfer reversal (`reverse_transfer(tx_id)`) from either `'AWAITING_CLEARING'` or `'SETTLED'` status to `'REVERSED'`, refunding `amount_cents + fee_cents` to `from_acct` and (when `'SETTLED'`) debiting `amount_cents` from `to_acct` only if `to_acct` has sufficient balance (`>= amount_cents`).
- Per-currency platform fee aggregation (`total_collected_fees(currency='USD')`) summing `fee_cents` across all non-reversed (`'SETTLED'` or `'AWAITING_CLEARING'`) transfers.
- Chronological per-account activity statements (`account_statement`) ordered deterministically by `(timestamp, insertion_index)` ascending.

## 2. Architecture
- **Single-Module Core Engine (`ledger_flow.py`)**: Encapsulates all account records, ordered transfer entries, and transaction lookup tables inside the `LedgerFlow` class with zero external dependencies.
- **Two-Plane Outer-Loop Specification Governance**:
  - **Specification Plane (`openspec/`)**: Milestone deltas (`ADDED`/`MODIFIED`/`REMOVED`/`RENAMED`) are staged in `openspec/changes/<milestone>/specs/ledger-flow/spec.md`, merged into `openspec/specs/ledger-flow/spec.md`, and archived under `openspec/changes/archive/<milestone>/`.
  - **Execution Plane (`conductor/`)**: Track plans (`conductor/tracks/milestone_1/plan.md` through `conductor/tracks/milestone_4/plan.md`) and technical constraints (`conductor/tech-stack.md`) govern task execution and constitutional scope boundaries.

## 3. Data Models & Schemas
### Account Record (`dict`)
| Field | Type | Constraints / Description |
| :--- | :--- | :--- |
| `account_id` | `str` | Trimmed non-empty unique identifier (`account_id.strip()`). |
| `currency` | `str` | Uppercase 3-letter ISO code in `{'USD', 'EUR', 'GBP'}`. |
| `balance` | `int` | Current available integer balance in cents (`>= 0`, overdrafts strictly prohibited). |
| `balance_cents` | `int` | Alias of `balance` in integer cents (`>= 0`). |
| `initial_cents` | `int` | Initial opening balance in integer cents (`>= 0`). |

### Transfer Entry Record (`dict`)
| Field | Type | Constraints / Description |
| :--- | :--- | :--- |
| `tx_id` | `str` | Trimmed non-empty unique transaction identifier. |
| `from_acct` | `str` | Sender account ID (must exist). |
| `to_acct` | `str` | Recipient account ID (must exist and differ from `from_acct`). |
| `amount_cents` | `int` | Principal transfer amount in integer cents (`> 0`). |
| `fee_cents` | `int` | Tiered platform fee in integer cents (`>= 10`). |
| `total_debit_cents` | `int` | Total debited from sender (`amount_cents + fee_cents`). |
| `currency` | `str` | Account currency (`'USD'`, `'EUR'`, or `'GBP'`). |
| `timestamp` | `int` | Integer epoch timestamp of transfer. |
| `status` | `str` | `'SETTLED'`, `'AWAITING_CLEARING'`, or `'REVERSED'`. |

## 4. Method Signatures & Contracts
1. `open_account(self, account_id: str, currency: str = 'USD', initial_cents: int = 0) -> dict`
   - **Preconditions**: `isinstance(account_id, str)` and `len(account_id.strip()) > 0`; trimmed `account_id` not already registered; `currency in {'USD', 'EUR', 'GBP'}`; `isinstance(initial_cents, int)` (not `bool`) and `initial_cents >= 0`.
   - **Postconditions**: Registers account with balance `initial_cents` and returns a copy of the account dictionary.
2. `get_balance(self, account_id: str) -> int`
   - **Preconditions**: `account_id` exists in registered accounts (`KeyError` otherwise).
   - **Postconditions**: Returns the current `int` balance in cents without mutating state.
3. `post_transfer(self, tx_id: str, from_acct: str, to_acct: str, amount_cents: int, timestamp: int) -> dict`
   - **Idempotency Pre-check**: If trimmed `tx_id` already exists in `self.transactions`:
     - If `(existing['from_acct'], existing['to_acct'], existing['amount_cents']) == (from_acct.strip(), to_acct.strip(), amount_cents)`, returns `dict(existing)` without mutating state.
     - Otherwise raises `ValueError('Conflicting tx_id')`.
   - **Preconditions**: `from_acct` and `to_acct` exist (`KeyError` otherwise); `tx_id` is a non-empty string (`ValueError` otherwise); `from_acct != to_acct`; `amount_cents > 0` (int, not bool); `from_acct` and `to_acct` share identical `currency`; `get_balance(from_acct) >= amount_cents + fee_cents` (`ValueError` on overdraft attempt).
   - **Postconditions**: Debits `amount_cents + fee_cents` from `from_acct` immediately. If `amount_cents >= 100000`, sets `status = 'AWAITING_CLEARING'` and does not credit `to_acct`. Otherwise sets `status = 'SETTLED'` and credits `amount_cents` to `to_acct` immediately. Returns a copy of the transfer dictionary.
4. `clear_transfer(self, tx_id: str) -> dict` (and backward-compatible alias `settle_pending(self, tx_id: str) -> dict`)
   - **Preconditions**: `tx_id` exists in `self.transactions` (`KeyError` otherwise); transfer `status == 'AWAITING_CLEARING'` (`ValueError` otherwise).
   - **Postconditions**: Sets transfer `status = 'SETTLED'`, credits `amount_cents` to `to_acct`, and returns a copy of the updated transfer dictionary.
5. `reverse_transfer(self, tx_id: str) -> dict`
   - **Preconditions**: `tx_id` exists in `self.transactions` (`KeyError` otherwise); transfer `status != 'REVERSED'` (`ValueError` otherwise). If `status == 'SETTLED'`, `get_balance(to_acct) >= amount_cents` (otherwise raises `ValueError('Recipient has insufficient funds to reverse')` without mutating state).
   - **Postconditions**: If `status == 'AWAITING_CLEARING'`, refunds `amount_cents + fee_cents` to `from_acct` and sets `status = 'REVERSED'`. If `status == 'SETTLED'`, debits `amount_cents` from `to_acct`, refunds `amount_cents + fee_cents` to `from_acct`, and sets `status = 'REVERSED'`. Returns a copy of the updated transfer dictionary.
6. `total_collected_fees(self, currency: str = 'USD') -> int`
   - **Preconditions**: `currency in {'USD', 'EUR', 'GBP'}` (`ValueError` otherwise).
   - **Postconditions**: Returns the `int` sum of `fee_cents` across all transfers with `entry['currency'] == currency` and `entry['status'] in ('SETTLED', 'AWAITING_CLEARING')`.
7. `account_statement(self, account_id: str) -> list[dict]`
   - **Preconditions**: `account_id` exists in registered accounts (`KeyError` otherwise).
   - **Postconditions**: Returns a list of defensive dictionary copies (`dict(entry)`) for all transfers where `from_acct == account_id` or `to_acct == account_id`, sorted ascending by `(timestamp, insertion_index)`.

## 5. State Machine & Fee/Clearing Workflows
- **Tiered Fee Calculation with 10-Cent Minimum Floor**:
  $$\text{fee\_cents} = \begin{cases} \max(10, \lfloor (\text{amount\_cents} \times 50) / 10000 \rfloor) & \text{if } \text{amount\_cents} \ge 100000 \\ \max(10, \lfloor \text{amount\_cents} / 100 \rfloor) & \text{if } \text{amount\_cents} < 100000 \end{cases}$$
- **Transfer Status Transitions (M1–M4)**:
  - `INITIATED` $\xrightarrow{\text{amount\_cents} < 100000}$ `SETTLED` (Immediate debit of `amount_cents + fee_cents` from `from_acct` and credit of `amount_cents` to `to_acct`).
  - `INITIATED` $\xrightarrow{\text{amount\_cents} \ge 100000}$ `AWAITING_CLEARING` (Immediate debit of `amount_cents + fee_cents` from `from_acct`; `to_acct` uncredited).
  - `AWAITING_CLEARING` $\xrightarrow{\text{clear\_transfer}(\text{tx\_id}) \text{ or } \text{settle\_pending}(\text{tx\_id})}$ `SETTLED` (Credits `amount_cents` to `to_acct`).
  - `AWAITING_CLEARING` $\xrightarrow{\text{reverse\_transfer}(\text{tx\_id})}$ `REVERSED` (Refunds `amount_cents + fee_cents` to `from_acct`).
  - `SETTLED` $\xrightarrow{\text{reverse\_transfer}(\text{tx\_id}) \text{ [if } \text{balance}(\text{to\_acct}) \ge \text{amount\_cents}\text{]}}$ `REVERSED` (Debits `amount_cents` from `to_acct` and refunds `amount_cents + fee_cents` to `from_acct`).

## 6. Error Contracts
| Method | Condition | Exception Raised |
| :--- | :--- | :--- |
| `open_account` | Empty/whitespace `account_id` or non-`str` | `ValueError` |
| `open_account` | Duplicate `account_id` (after trimming) | `ValueError` |
| `open_account` | `currency` not in `{'USD', 'EUR', 'GBP'}` | `ValueError` |
| `open_account` | `initial_cents < 0` or non-`int` / `bool` | `ValueError` |
| `get_balance` | `account_id` does not exist | `KeyError` |
| `post_transfer` | Existing `tx_id` with different `(from_acct, to_acct, amount_cents)` | `ValueError('Conflicting tx_id')` |
| `post_transfer` | `from_acct` or `to_acct` does not exist | `KeyError` |
| `post_transfer` | Empty/whitespace `tx_id` or non-`str` | `ValueError` |
| `post_transfer` | `from_acct == to_acct` | `ValueError` |
| `post_transfer` | `amount_cents <= 0` or non-`int` / `bool` | `ValueError` |
| `post_transfer` | Currency mismatch between `from_acct` and `to_acct` | `ValueError` |
| `post_transfer` | Insufficient funds (`balance < amount_cents + fee_cents`) | `ValueError` |
| `clear_transfer` / `settle_pending` | `tx_id` does not exist | `KeyError` |
| `clear_transfer` / `settle_pending` | Transfer `status != 'AWAITING_CLEARING'` (e.g. `'SETTLED'` or `'REVERSED'`) | `ValueError` |
| `reverse_transfer` | `tx_id` does not exist | `KeyError` |
| `reverse_transfer` | Transfer `status == 'REVERSED'` | `ValueError` |
| `reverse_transfer` | Transfer `status == 'SETTLED'` and `balance(to_acct) < amount_cents` | `ValueError('Recipient has insufficient funds to reverse')` |
| `total_collected_fees` | `currency` not in `{'USD', 'EUR', 'GBP'}` | `ValueError` |
| `account_statement` | `account_id` does not exist | `KeyError` |

## 7. Directory Layout
```text
workspace/
├── SPEC.md                                          # 8-Section Clean-Room SSOT
├── ledger_flow.py                                   # Core LedgerFlow implementation
├── test_ledger_flow.py                              # Locked unittest regression suite
├── conductor/
│   ├── tech-stack.md                                # Runtime and architectural constraints
│   └── tracks/
│       ├── milestone_1/plan.md                      # M1 5-Step Scorecard & Out of Scope
│       ├── milestone_2/plan.md                      # M2 5-Step Scorecard & Out of Scope
│       ├── milestone_3/plan.md                      # M3 5-Step Scorecard & Out of Scope
│       └── milestone_4/plan.md                      # M4 5-Step Scorecard & Out of Scope
└── openspec/
    ├── specs/
    │   └── ledger-flow/
    │       └── spec.md                              # Merged canonical living specification
    └── changes/
        ├── m1/specs/ledger-flow/spec.md             # Staged M1 delta
        ├── m2/specs/ledger-flow/spec.md             # Staged M2 delta
        ├── m3/specs/ledger-flow/spec.md             # Staged M3 delta
        ├── m4/specs/ledger-flow/spec.md             # Staged M4 delta
        └── archive/
            ├── m1/specs/ledger-flow/spec.md         # Archived M1 delta
            ├── m2/specs/ledger-flow/spec.md         # Archived M2 delta
            ├── m3/specs/ledger-flow/spec.md         # Archived M3 delta
            └── m4/specs/ledger-flow/spec.md         # Archived M4 delta
```

## 8. Binary Acceptance Criteria
- [x] **AC-1**: `open_account` trims `account_id`, enforces `currency in {'USD', 'EUR', 'GBP'}` and `initial_cents >= 0`, and raises `ValueError` on invalid input or duplicate `account_id`.
- [x] **AC-2**: `get_balance` returns exact `int` balance in cents and raises `KeyError` for unknown accounts.
- [x] **AC-3**: `post_transfer` enforces strict no-overdraft (`balance >= amount_cents + fee_cents`), is replay-safe idempotent on identical `(tx_id, from_acct, to_acct, amount_cents)`, and raises `ValueError('Conflicting tx_id')` on parameter mismatch.
- [x] **AC-4**: `post_transfer` charges `max(10, (amount_cents * 50) // 10000)` when `amount_cents >= 100000` (setting `status = 'AWAITING_CLEARING'`) and `max(10, amount_cents // 100)` when `amount_cents < 100000` (setting `status = 'SETTLED'`).
- [x] **AC-5**: `clear_transfer` (and alias `settle_pending`) transitions `'AWAITING_CLEARING'` transfers to `'SETTLED'`, credits `amount_cents` to `to_acct`, raises `KeyError` for unknown `tx_id`, and raises `ValueError` if not `'AWAITING_CLEARING'`.
- [x] **AC-6**: `reverse_transfer` transitions `'AWAITING_CLEARING'` or `'SETTLED'` transfers to `'REVERSED'`, refunds `amount_cents + fee_cents` to `from_acct`, debits `amount_cents` from `to_acct` when `'SETTLED'` (raising `ValueError('Recipient has insufficient funds to reverse')` without mutating state if `to_acct` balance `< amount_cents`), and raises `KeyError` if `tx_id` is unknown or `ValueError` if already `'REVERSED'`.
- [x] **AC-7**: `total_collected_fees(currency='USD')` returns the sum of `fee_cents` across all non-reversed (`'SETTLED'` or `'AWAITING_CLEARING'`) transfers in `currency`.
- [x] **AC-8**: `account_statement` raises `KeyError` for unknown `account_id` and otherwise returns defensive copies of all transfers involving `account_id` sorted ascending by `(timestamp, insertion_index)`.
- [x] **AC-9**: `python3 -m unittest` passes with exit code `0`.
