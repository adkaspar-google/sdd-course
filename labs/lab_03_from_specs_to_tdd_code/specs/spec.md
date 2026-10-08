# Circuit Breaker Capability Specification

## Purpose
The `circuit-breaker` capability prevents cascading failures across distributed service calls by wrapping downstream callables in a deterministic `CLOSED -> OPEN -> HALF_OPEN` state machine.

## Requirements

### Requirement: Closed State Call Forwarding (REQ-0001)
The circuit breaker SHALL initialize in the `CLOSED` state with `consecutive_failures=0` and SHALL execute wrapped callables, returning their result directly.

#### Scenario: Healthy call succeeds in CLOSED state
- **GIVEN** a newly initialized `CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30.0)`
- **WHEN** `call(lambda: "ok")` is invoked
- **THEN** the breaker MUST return `"ok"` and remain in `CircuitState.CLOSED`

### Requirement: Failure Threshold Trip to OPEN (REQ-0002)
When `consecutive_failures` reaches `failure_threshold` in the `CLOSED` state, the circuit breaker SHALL transition immediately to `CircuitState.OPEN`, record `opened_at = now`, and re-raise the underlying exception.

#### Scenario: Reaching failure threshold trips breaker to OPEN
- **GIVEN** a `CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30.0)` in `CLOSED` state
- **WHEN** `3` consecutive calls raise `RuntimeError("downstream timeout")`
- **THEN** after the 3rd failure the state MUST be `CircuitState.OPEN` with `consecutive_failures=3`

### Requirement: Fast-Fail Rejection While OPEN (REQ-0003)
While in `CircuitState.OPEN` and `now - opened_at < recovery_timeout_seconds`, the circuit breaker SHALL raise `CircuitOpenError` immediately without invoking the wrapped callable.

#### Scenario: Calls during open cooldown fail fast without invoking target
- **GIVEN** a breaker in `CircuitState.OPEN` opened at `t=100.0` with `recovery_timeout_seconds=30.0`
- **WHEN** a caller invokes `call(fn)` at `t=115.0`
- **THEN** `CircuitOpenError` MUST be raised and `fn` MUST NOT be executed (`call_count == 0`)

### Requirement: Automatic Cooldown Transition to HALF_OPEN (REQ-0004)
When the breaker is in `CircuitState.OPEN` and `now - opened_at >= recovery_timeout_seconds`, the circuit breaker SHALL transition to `CircuitState.HALF_OPEN` and allow a probe call to execute.

#### Scenario: Cooldown expiry transitions state to HALF_OPEN
- **GIVEN** a breaker opened at `t=100.0` with `recovery_timeout_seconds=30.0`
- **WHEN** `state` is inspected or `call()` is invoked at `t=130.0`
- **THEN** the breaker MUST transition to `CircuitState.HALF_OPEN`

### Requirement: Probe Success Closes Circuit (REQ-0005)
When a probe call succeeds in `CircuitState.HALF_OPEN`, the circuit breaker SHALL transition to `CircuitState.CLOSED` and reset `consecutive_failures = 0`.

#### Scenario: Successful probe in HALF_OPEN restores CLOSED state
- **GIVEN** a breaker in `CircuitState.HALF_OPEN` at `t=130.0`
- **WHEN** `call(lambda: 200)` succeeds
- **THEN** the breaker MUST return `200`, transition to `CircuitState.CLOSED`, and set `consecutive_failures=0`

### Requirement: Probe Failure Re-Opens Circuit (REQ-0006)
When a probe call raises an exception in `CircuitState.HALF_OPEN`, the circuit breaker SHALL immediately transition back to `CircuitState.OPEN`, update `opened_at = now` to restart the cooldown window, and re-raise the exception.

#### Scenario: Failed probe in HALF_OPEN re-opens breaker and resets timer
- **GIVEN** a breaker in `CircuitState.HALF_OPEN` at `t=130.0` (`recovery_timeout_seconds=30.0`)
- **WHEN** `call(failing_fn)` raises `ConnectionError`
- **THEN** the breaker MUST transition to `CircuitState.OPEN` and reject calls with `CircuitOpenError` until `t=160.0`

### Requirement: Success in CLOSED Resets Failure Streak (REQ-0007)
When a call succeeds in `CircuitState.CLOSED` after fewer than `failure_threshold` failures, the circuit breaker SHALL reset `consecutive_failures` to `0`.

#### Scenario: Intermittent failure followed by success does not accumulate toward trip
- **GIVEN** a breaker with `failure_threshold=3` that has recorded `2` consecutive failures
- **WHEN** the next call succeeds, followed by `2` more failures
- **THEN** `consecutive_failures` MUST be `2` and the state MUST remain `CircuitState.CLOSED`
