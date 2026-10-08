# Lab 05: SDD Code Review, Spec Synchronization & Stacked PR Task Decomposition

**Estimated Time**: 40–50 minutes  
**Frameworks Practiced**: Conductor (`/conductor:review`) + OpenSpec (`/opsx:verify` + `/opsx:archive` Stacked PR Batches)

---

## 1. Learning Objective
In Spec-Driven Development, **code review starts with the specification diff, not the source code diff**. When a contributor submits a PR that silently changes core algorithmic behavior (e.g., switching a cache from FIFO to LRU eviction) and adds a new public API (`put_with_ttl`) without updating `openspec/specs/` or writing `test_reqXXXX_*` tests, SDD review immediately blocks the change.

In this hands-on lab, you will:
1. **Audit a Subpar Code Change (`simulated_review/subpar_change.patch`)** against the baseline specification (`base/openspec/specs/kv-cache/spec.md`) and baseline code (`base/kvcache.py`).
2. **Identify the 3 SDD Review Violations**:
   - **Violation 1 (Silent Behavioral Contradiction)**: The patch changes `get()` to call `move_to_end(key)` (converting FIFO eviction into LRU eviction), directly violating `REQ-0002` (FIFO eviction order).
   - **Violation 2 (Un-Specced Public API)**: The patch adds `put_with_ttl(key, value, ttl_seconds)` without adding `REQ-0006` to `openspec/specs/kv-cache/spec.md` or updating `design.md`.
   - **Violation 3 (Missing Requirement Test Traceability)**: No `test_req0006_*` unit test was added, and `ttl_seconds <= 0` validation is missing.
3. **Remediate & Structure as Stacked PR Batches**:
   - Update `expected_output/openspec/specs/kv-cache/spec.md` (preserving `REQ-0002` FIFO eviction and adding `REQ-0006` Per-Entry TTL Expiration).
   - Structure `expected_output/tasks.md` into **Stacked PR Batches** (`Batch 1: Spec & TTL State`, `Batch 2: Lazy + Eager TTL Eviction & Tests`, `Archive PR N+1`).
   - Implement the clean, compliant `expected_output/kvcache.py` and `expected_output/test_kvcache.py`.

---

## 2. Self-Diagnosis & Grading
Run `./self_diagnose.sh` to verify the synchronized specification, Stacked PR task batches, and unit tests:

```bash
./self_diagnose.sh
```
