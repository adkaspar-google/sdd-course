# Brownfield Architecture Recovery: Distributed Lease Lock Manager

## Recovered Component Invariants
1. **Lazy + Eager Expiration**: Expired leases are purged lazily on every per-resource operation (`_purge_if_expired`) and eagerly via `evict_expired()`.
2. **Global Monotonic Token Counter**: `_next_token` increments on every `acquire()` and `renew()`, preventing ABA token reuse.
3. **Token-Guarded Mutations**: Both `renew()` and `release()` require the caller to present the exact active `fencing_token`, preventing stale holders from accidentally releasing or extending a successor's lease.
