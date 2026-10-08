# Track Specification: Greenfield Distributed Rate Limiter (`rate_limiter_mvp`)

## 1. Overview
Build a deterministic, thread-safe sliding-window rate limiter (`SlidingWindowRateLimiter`) that enforces per-key request quotas with variable request costs and exact retry-after calculation.

## 2. Architecture & Component Topology
- **Module**: `ratelimiter.py`
- **Value Object**: `RateLimitDecision(allowed: bool, remaining: int, retry_after_seconds: float)`
- **Core Class**: `SlidingWindowRateLimiter(limit: int, window_seconds: float, clock: Callable[[], float])`
- **Synchronization**: Internal `threading.RLock` protecting `dict[str, deque[tuple[float, int]]]`.

## 3. Functional Requirements
- **REQ-0001**: Admit requests when active window cost + `cost <= limit` after evicting entries with `timestamp <= now - window_seconds`.
- **REQ-0002**: Reject requests when active window cost + `cost > limit` and return the exact `retry_after_seconds` until enough oldest entries expire.
- **REQ-0003**: Validate `limit >= 1`, `window_seconds > 0`, non-empty `key`, and `1 <= cost <= limit` (`ValueError` on invalid input).
- **REQ-0004**: Support injectable `clock` callable for zero-sleep deterministic tests.
- **REQ-0005**: Guarantee thread-safe atomic evaluation under concurrent callers.
- **REQ-0006**: Support `reset(key)` to clear a single tenant's history.

## 4. Non-Functional Requirements
- Zero external third-party packages (Python 3.11+ standard library only).
- Full unit test suite execution time `< 100ms`.
- Requirement test coverage `100%` (`REQ-0001` through `REQ-0006`).

## 5. Acceptance Criteria
- [x] `REQ-0001` verified by `test_req0001_sliding_window_allowance_and_expiry`
- [x] `REQ-0002` verified by `test_req0002_rejection_and_exact_retry_after`
- [x] `REQ-0003` verified by `test_req0003_validation_errors`
- [x] `REQ-0004` verified by `test_req0004_injectable_clock_determinism`
- [x] `REQ-0005` verified by `test_req0005_thread_safe_concurrency`
- [x] `REQ-0006` verified by `test_req0006_key_reset_isolation`

## 6. Out of Scope
- External Redis/Memcached network adapters.
- HTTP middleware framework bindings (FastAPI/Flask decorators).

## 7. Verification Commands
```bash
CI=true python3 -m unittest discover -s expected_output -p "test_*.py" -v
```
