# Token Bucket Quota Allocator Specification

## Purpose
The `quota-allocator` capability enforces per-tenant token-bucket rate and burst quotas with integer token accounting and deterministic fractional time preservation.

## Requirements

### Requirement: Initial Bucket Capacity Allocation (REQ-0001)
Each new tenant key SHALL initialize with `tokens = capacity` and `last_replenished = now`.

#### Scenario: First consumption for a new tenant starts from full capacity
- **GIVEN** `capacity=10` and `refill_rate_per_sec=1.0`
- **WHEN** new tenant `"t-1"` calls `consume("t-1", amount=4)` at `t=0.0`
- **THEN** the call MUST return `True` and `available_tokens("t-1")` MUST be `6`

### Requirement: Atomic Token Consumption (REQ-0002)
When `available_tokens >= amount`, `consume(key, amount)` SHALL deduct `amount` tokens and return `True`; otherwise it SHALL leave `tokens` unchanged and return `False`.

#### Scenario: Insufficient tokens leaves bucket balance untouched
- **GIVEN** tenant `"t-1"` has `3` tokens remaining
- **WHEN** `"t-1"` calls `consume("t-1", amount=5)`
- **THEN** the call MUST return `False` and `available_tokens("t-1")` MUST remain `3`

### Requirement: Linear Refill Capped at Capacity (REQ-0003)
Tokens SHALL replenish at `refill_rate_per_sec` over elapsed time up to a maximum of `capacity`.

#### Scenario: Long idle period caps tokens at capacity
- **GIVEN** `"t-1"` has `0` tokens at `t=0.0` with `capacity=10, refill_rate_per_sec=2.0`
- **WHEN** the clock advances to `t=100.0`
- **THEN** `available_tokens("t-1")` MUST be `10` (never exceeding `capacity`)

### Requirement: Input Boundary Validation (REQ-0004)
The allocator SHALL raise `ValueError` if `capacity < 1`, `refill_rate_per_sec <= 0`, `key` is empty, or `amount < 1`.

#### Scenario: Non-positive consume amount raises ValueError
- **GIVEN** an initialized allocator
- **WHEN** `consume("t-1", amount=0)` is called
- **THEN** `ValueError` MUST be raised

### Requirement: Fractional Elapsed Time Preservation Across Sub-Quantum Polls (REQ-0005)
When `_replenish` is evaluated after a sub-quantum interval where `int(elapsed * refill_rate_per_sec) == 0`, the allocator SHALL NOT overwrite `last_replenished = now`; when `added > 0`, `last_replenished` SHALL advance by `added / refill_rate_per_sec` (or to `now` when `tokens == capacity`) so fractional time remainder is never lost.

#### Scenario: Frequent sub-second polling still accumulates whole tokens
- **GIVEN** `"t-1"` has `0` tokens at `t=0.0` with `capacity=5, refill_rate_per_sec=1.0`
- **WHEN** `"t-1"` calls `consume("t-1", 1)` at `t=0.4`, `t=0.8`, and `t=1.2`
- **THEN** the calls at `t=0.4` and `t=0.8` MUST return `False`, and the call at `t=1.2` MUST replenish `1` token and return `True`

### Requirement: Thread-Safe Synchronization (REQ-0006)
All bucket reads and mutations SHALL be protected by a `threading.RLock`.

#### Scenario: Concurrent consumption never produces negative token balances
- **GIVEN** `"t-1"` has `10` tokens
- **WHEN** `20` threads concurrently call `consume("t-1", 1)`
- **THEN** exactly `10` calls return `True` and `available_tokens("t-1")` equals `0`
