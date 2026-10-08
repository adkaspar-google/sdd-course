# Technical Design: Bounded FIFO Cache with Per-Entry TTL (`REQ-0006`)

## SDD Review Remediation Summary
1. **Rejected Silent FIFO -> LRU Mutation**: Preserved strict FIFO insertion order (`REQ-0002`) by removing `self._store.move_to_end(key)` from `get()`.
2. **Added Formal `REQ-0006` Specification**: Specified `put_with_ttl(key, value, ttl_seconds)` with `ttl_seconds > 0` validation, injectable `clock`, and pre-eviction expired-entry purging.
3. **Internal Entry Representation**: Each key maps to `_CacheEntry(value: Any, expires_at: Optional[float])`.
