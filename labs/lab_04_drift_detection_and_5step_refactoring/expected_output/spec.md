# Track Specification: Fix Zero-Token Timestamp Drift (`quota_zero_token_fix`)

## 1. Overview
Remediate Scorecard Finding **F-01** (`REQ-0005` spec drift) in `TokenBucketQuotaAllocator._replenish()` where sub-quantum polling (`added == 0`) prematurely advances `bucket.last_replenished = now` and starves token refill.

## 2. Architecture & Component Topology
- **Target File**: `service/quota_allocator.py` -> `TokenBucketQuotaAllocator._replenish`
- **State Invariant**: `bucket.last_replenished` represents the timestamp corresponding to the last integer token credited to `bucket.tokens`.

## 3. Functional Requirements
- **REQ-0005**: When `added == 0`, `_replenish()` MUST NOT modify `bucket.last_replenished`. When `added > 0`, `_replenish()` SHALL advance `bucket.last_replenished` by `added / refill_rate_per_sec` (or set it to `now` if `bucket.tokens` reaches `capacity`).

## 4. Non-Functional Requirements
- Maintain $O(1)$ time and space complexity per `_replenish()` call.
- Zero regression across `REQ-0001` through `REQ-0006`.

## 5. Acceptance Criteria
- [x] `test_req0005_sub_quantum_polling_preserves_fractional_elapsed_time` fails on `service/quota_allocator.py` (Red) and passes on `expected_output/quota_allocator_fixed.py` (Green).

## 6. Out of Scope
- **F-02**: Prometheus counter hooks for rejected quota requests.
- **F-03**: Background TTL compaction of idle tenant buckets.
- **F-04**: Batch `consume_many(keys)` API helper.

## 7. Verification Commands
```bash
CI=true python3 -m unittest discover -s expected_output -p "test_*.py" -v
```
