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

---

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Spec Compliance & Bug Review**:
   - Run `/conductor:conductor-review` and `/opsx:verify` for spec compliance, then `/code-review` for bugs, with the instruction to report only requirement or correctness gaps.
   - Run `/opsx:propose` and `/conductor:conductor-new-track` to synchronize `REQ-0006` in `labs/lab_05_sdd_code_review_and_stacked_prs/work/openspec/specs/kv-cache/spec.md` and decompose the work into Stacked PR batches in `labs/lab_05_sdd_code_review_and_stacked_prs/work/tasks.md`.
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Clean Implementation Session**: Start a new session (or run `/clear`) before implementing.
5. **Set Goal & Implement**: Set the session goal and run `/conductor:conductor-implement` and `/opsx:apply` to write `kvcache.py` and `test_kvcache.py` under `labs/lab_05_sdd_code_review_and_stacked_prs/work/`:
   ```text
   /goal ./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh work exits 0, shown by running it; no file under adversarial_tests/ or expected_output/ is modified; or stop after 20 turns.
   ```
6. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh work
   ```
