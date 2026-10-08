# TDD Implementation Tasks (`circuit-breaker`)

## Batch 1: Core State Machine & CLOSED/OPEN Transitions
- [x] 1.1 Write `test_req0001_closed_state_forwards_calls` and `test_req0007_success_resets_failure_streak`, then implement `CLOSED` state execution (`REQ-0001`, `REQ-0007`).
- [x] 1.2 Write `test_req0002_failure_threshold_trips_to_open` and `test_req0003_open_state_fails_fast_without_invoking_callable`, then implement `OPEN` trip and `CircuitOpenError` (`REQ-0002`, `REQ-0003`).

## Batch 2: Cooldown Probing (`HALF_OPEN`) & Recovery
- [x] 2.1 Write `test_req0004_cooldown_transitions_to_half_open`, `test_req0005_probe_success_closes_circuit`, and `test_req0006_probe_failure_reopens_circuit`, then implement `HALF_OPEN` probe transitions (`REQ-0004`, `REQ-0005`, `REQ-0006`).
