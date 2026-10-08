# ADR-0001: Rate Limiter Storage Engine Selection

- **Status**: Accepted
- **Related Requirements**: `REQ-0001`, `REQ-0004`, `REQ-0005`

## Context
We must select the state storage engine for the reference rate limiter used across local development, CI verification, and single-node edge gateways.

## Options Evaluated

| Criterion | Option A: In-Memory `deque` + `RLock` | Option B: Redis Sorted Sets (`ZSET`) | Option C: PostgreSQL Row Locks |
| :--- | :--- | :--- | :--- |
| **Latency (p99)** | `< 10 microseconds` | `1.5 - 3.0 ms` (network RTT) | `5 - 20 ms` (disk + lock contention) |
| **Zero-Dependency CI** | Yes (Python stdlib) | No (requires Redis daemon) | No (requires PostgreSQL) |
| **Multi-Node Shared State** | Single-process only | Native cluster-wide state | Cluster-wide with high contention |

## Decision
We choose **Option A (In-Memory `deque` + `threading.RLock`)** for the core `SlidingWindowRateLimiter` domain engine, with an injectable clock (`REQ-0004`). Multi-node deployments can implement the same interface using Redis Lua scripts without changing caller contracts.
