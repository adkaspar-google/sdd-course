# Brownfield Code Quality Scorecard (`quota_allocator.py`)

**Audit Date**: 2026-10-08  
**Component**: `service/quota_allocator.py`

| Finding ID | Severity | Category | Description | Target Track |
| :--- | :--- | :--- | :--- | :--- |
| **F-01** | **CRITICAL** | Spec Drift (`REQ-0005`) | `_replenish()` overwrites `bucket.last_replenished = now` even when `added == 0` (sub-quantum elapsed interval), starving token replenishment under frequent polling. | **Track 1 (`quota_zero_token_fix`) — THIS LAB** |
| **F-02** | MEDIUM | Observability | Missing Prometheus counter hook for rejected quota requests. | Deferred (Track 2 — Out of Scope for Track 1) |
| **F-03** | LOW | Memory Hygiene | Inactive tenant buckets without activity for `>24h` are not background-compacted. | Deferred (Track 3 — Out of Scope for Track 1) |
| **F-04** | LOW | API Ergonomics | Add batch `consume_many(keys)` helper for bulk ingestion jobs. | Deferred (Track 4 — Out of Scope for Track 1) |
