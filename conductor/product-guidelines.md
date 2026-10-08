# Product Guidelines

## Architectural Invariants
1. **Spec-Before-Code**: No production module may be created or modified without a corresponding requirement (`REQ-XXXX`) in `openspec/specs/` or `conductor/tracks/<track_id>/spec.md`.
2. **Traceable Verification**: Every unit test MUST reference the requirement ID it verifies (e.g., `test_req0001_...`).
3. **Deterministic Time & Concurrency**: All time-sensitive components (rate limiters, lease locks, circuit breakers, quota allocators, TTL caches) MUST accept an injectable `clock` callable (`Callable[[], float]`) so unit tests execute deterministically in `<50ms` without `time.sleep()`.
4. **Zero Unapproved Dependencies**: All hands-on labs use the Python 3.11+ Standard Library (`unittest`, `threading`, `dataclasses`, `enum`, `collections`) so students can run every lab offline without external package setup.
