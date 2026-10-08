# Stacked PR Task Decomposition (`add-kvcache-ttl`)

## Batch 1 (PR 1/3 — ~120 LOC): Spec Delta & `_CacheEntry` Clock Plumbing
- **Depends On**: None
- [x] 1.1 Add `REQ-0006` (`put_with_ttl`) to `openspec/specs/kv-cache/spec.md` while keeping `REQ-0002` FIFO invariant intact.
- [x] 1.2 Add injectable `clock: Callable[[], float] = time.monotonic` and `_CacheEntry(value, expires_at)` to `KVCache`.

## Batch 2 (PR 2/3 — ~140 LOC): TTL Expiration & Traceable Unit Tests (`REQ-0001`..`REQ-0006`)
- **Depends On**: Batch 1
- [x] 2.1 Implement `put_with_ttl` validation (`ttl_seconds > 0`) and `_purge_expired(now)` before FIFO eviction.
- [x] 2.2 Add `test_req0001_...` through `test_req0006_...` in `test_kvcache.py`.

## Archive PR N+1 (PR 3/3): OpenSpec Verification & Archive
- **Depends On**: Batch 2
- [x] 3.1 Run `/opsx:verify` and `/opsx:archive` to promote `REQ-0006` into canonical `openspec/specs/kv-cache/spec.md`.
