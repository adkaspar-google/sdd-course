# Technical Design: Circuit Breaker State Machine

## State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> CLOSED: Call Succeeds (reset failures=0, REQ-0007)\nOR Failure < failure_threshold
    CLOSED --> OPEN: Failure == failure_threshold (REQ-0002)
    OPEN --> OPEN: Call while now - opened_at < timeout\nRaise CircuitOpenError (REQ-0003)
    OPEN --> HALF_OPEN: now - opened_at >= timeout (REQ-0004)
    HALF_OPEN --> CLOSED: Probe Succeeds (reset failures=0, REQ-0005)
    HALF_OPEN --> OPEN: Probe Fails (opened_at = now, REQ-0006)
```

## Concurrency & Determinism
- Protected by `threading.RLock`.
- Accepts injectable `clock: Callable[[], float] = time.monotonic`.
