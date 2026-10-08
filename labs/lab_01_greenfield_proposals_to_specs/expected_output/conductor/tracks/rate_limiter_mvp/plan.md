# Implementation Plan: Greenfield Distributed Rate Limiter (`rate_limiter_mvp`)

## Phase 1: Core Sliding-Window Contract & Validation [checkpoint: a101f01]
- [x] Task: Scaffold `RateLimitDecision` and constructor validation (`REQ-0003`, `REQ-0004`) 11a01b2
- [x] Task: Implement sliding-window eviction, allowance, and exact `retry_after_seconds` (`REQ-0001`, `REQ-0002`) 22b02c3
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Sliding-Window Contract & Validation' (Protocol in workflow.md)

## Phase 2: Concurrency Safety & Administrative Reset [checkpoint: b202f02]
- [x] Task: Add `threading.RLock` synchronization and `reset(key)` isolation (`REQ-0005`, `REQ-0006`) 33c03d4
- [x] Task: Conductor - User Manual Verification 'Phase 2: Concurrency Safety & Administrative Reset' (Protocol in workflow.md)
