# ADR-0001: Monotonic Fencing Tokens for Lease Lock Safety

- **Status**: Accepted (Recovered from Brownfield Implementation)
- **Related Requirements**: `REQ-0002`, `REQ-0004`, `REQ-0005`

## Context
When Worker A acquires a time-bounded lease (`ttl_seconds=10.0`) and experiences a long stop-the-world GC pause or network delay (`12.0s`), its lease expires and Worker B acquires the lease. Without fencing tokens, Worker A wakes up and overwrites Worker B's downstream storage state.

## Decision
Every lease acquisition and renewal issues a globally monotonic integer `fencing_token`. Downstream storage systems and `LeaseManager.renew`/`release` verify `fencing_token` equality/monotonicity and reject stale tokens (`REQ-0002`, `REQ-0005`).
