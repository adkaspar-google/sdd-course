# Rate Limiter Capability Specification

## Purpose
The `rate-limiter` capability enforces deterministic, thread-safe per-key sliding-window rate limiting with configurable request cost, exact retry-after calculation, and injectable clock support so API endpoints remain protected against tenant burst traffic.

## Requirements

### Requirement: Sliding Window Request Allowance (REQ-0001)
The system SHALL allow a request for `key` with integer `cost >= 1` when the sum of non-expired request costs within `[now - window_seconds, now]` plus `cost` is less than or equal to `limit`.

#### Scenario: Requests within sliding window limit are allowed
- **GIVEN** a rate limiter configured with `limit=5` and `window_seconds=60.0` at `t=100.0`
- **WHEN** client `"tenant-a"` sends a request with `cost=3` at `t=100.0`
- **THEN** the system MUST return `allowed=True`, `remaining=2`, and `retry_after_seconds=0.0`

#### Scenario: Expired timestamps outside the sliding window are evicted
- **GIVEN** client `"tenant-a"` consumed `5` units at `t=100.0` (`limit=5, window_seconds=60.0`)
- **WHEN** client `"tenant-a"` sends a request with `cost=2` at `t=160.1`
- **THEN** the expired consumption at `t=100.0` MUST be evicted and the system MUST return `allowed=True` with `remaining=3`

### Requirement: Quota Exhaustion and Retry-After Calculation (REQ-0002)
When a request's `cost` would cause the active sliding-window usage for `key` to exceed `limit`, the system SHALL reject the request (`allowed=False`), leave existing usage unchanged, and compute `retry_after_seconds` as the exact time until enough oldest entries expire to admit `cost`.

#### Scenario: Request exceeding remaining quota is rejected with exact retry delay
- **GIVEN** a rate limiter with `limit=5, window_seconds=60.0` where `"tenant-a"` consumed `3` units at `t=100.0` and `2` units at `t=110.0`
- **WHEN** `"tenant-a"` requests `cost=2` at `t=120.0`
- **THEN** the system MUST return `allowed=False`, `remaining=0`, and `retry_after_seconds=40.0` (when the 3 units from `t=100.0` expire at `t=160.0`)

### Requirement: Configuration and Cost Boundary Validation (REQ-0003)
The system SHALL validate that `limit >= 1`, `window_seconds > 0`, `key` is a non-empty string, and `cost >= 1` (and `cost <= limit`), raising `ValueError` on any violation.

#### Scenario: Invalid configuration parameters raise ValueError
- **GIVEN** a caller attempts to instantiate the rate limiter with `limit=0` or `window_seconds=-5.0`
- **WHEN** initialization executes
- **THEN** the system MUST raise `ValueError`

### Requirement: Deterministic Clock Injection (REQ-0004)
The system SHALL accept an injectable `clock: Callable[[], float]` parameter (defaulting to `time.monotonic`) and MUST use it for all window boundary evaluations without calling `time.sleep()`.

#### Scenario: Advancing injected fake clock expires window entries deterministically
- **GIVEN** a rate limiter bound to a mutable test clock starting at `t=0.0`
- **WHEN** the test clock is advanced to `t=61.0`
- **THEN** all entries recorded at `t=0.0` for `window_seconds=60.0` MUST be treated as expired immediately

### Requirement: Thread-Safe Concurrent Evaluation (REQ-0005)
All state mutations and window evaluations across keys SHALL be synchronized with a re-entrant lock (`threading.RLock`) so concurrent threads cannot oversubscribe a key's `limit`.

#### Scenario: Concurrent threads racing on the same key never exceed limit
- **GIVEN** a rate limiter with `limit=10, window_seconds=60.0`
- **WHEN** `25` concurrent worker threads simultaneously call `allow("shared-key", cost=1)`
- **THEN** at most `10` calls MUST return `allowed=True` and `15` calls MUST return `allowed=False`

### Requirement: Administrative Key Quota Reset (REQ-0006)
The system SHALL provide a `reset(key: str)` method that atomically clears all recorded consumption for `key` without affecting other keys.

#### Scenario: Resetting an exhausted key restores full quota
- **GIVEN** `"tenant-a"` has `remaining=0` and `"tenant-b"` has `remaining=2`
- **WHEN** `reset("tenant-a")` is invoked
- **THEN** `"tenant-a"` MUST immediately have `remaining=limit` while `"tenant-b"` retains `remaining=2`
