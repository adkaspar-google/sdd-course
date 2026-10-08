# Lab 04: Spec-to-Code Drift Detection & The 5-Step Brownfield Scorecard Refactoring Loop

**Estimated Time**: 40–50 minutes  
**Frameworks Practiced**: OpenSpec (`/opsx:verify`) + Conductor (`/conductor:newTrack` + `/conductor:implement`) + 5-Step Brownfield Scorecard Refactoring

---

## 1. Learning Objective
In brownfield production systems, two forces degrade software quality over time:
1. **Silent Spec-to-Code Drift**: A developer modifies production code without updating the specification (or introduces a subtle state bug that violates an existing `REQ-XXXX` invariant).
2. **Accumulated Technical Debt**: Structural findings accumulate across a codebase, and attempting to fix all of them in a single "mega-prompt" causes catastrophic regressions.

In this lab, you will practice both:
1. **Detect & Fix Spec Drift (`REQ-0005`)**: Inspect `specs/spec.md` vs. `service/quota_allocator.py`. Discover why calling `_replenish()` when `added_tokens == 0` prematurely overwrites `last_replenished = now` and permanently starves fractional token accumulation (`REQ-0005`).
2. **Execute the 5-Step Brownfield Scorecard Refactoring Loop**: Review `scorecard.md` (Findings `F-01` through `F-04`), isolate `F-01` (`REQ-0005` zero-token timestamp drift) into a surgical Conductor track (`expected_output/spec.md`) with `F-02..F-04` explicitly listed under **Out of Scope**, and verify the fix with a regression test.

---

## 2. Starting Input
- [`specs/spec.md`](./specs/spec.md): Normative specification for `TokenBucketQuotaAllocator` (`REQ-0001`..`REQ-0006`).
- [`service/quota_allocator.py`](./service/quota_allocator.py): Bugged implementation containing the `REQ-0005` fractional replenishment starvation bug.
- [`scorecard.md`](./scorecard.md): Engineering Audit Scorecard containing 4 findings (`F-01` through `F-04`).

---

## 3. Hands-On Exercise Steps

### Step 1: Audit `service/quota_allocator.py` Against `REQ-0005`
Look closely at `_replenish` in `service/quota_allocator.py`:
```python
elapsed = max(0.0, now - bucket.last_replenished)
added = int(elapsed * self._refill_rate_per_sec)
bucket.tokens = min(self._capacity, bucket.tokens + added)
bucket.last_replenished = now  # <-- BUG when added == 0!
```
If `refill_rate_per_sec = 1.0` and a caller polls `consume()` every `0.4` seconds, `int(0.4 * 1.0) == 0`, yet `bucket.last_replenished` is overwritten to `now` on every poll—so the bucket **never** replenishes a single token!

### Step 2: Author the Surgical Track `spec.md` (`F-01` Only)
Create a 7-section Conductor track specification (`expected_output/spec.md`) that scopes `F-01` (`REQ-0005`) and places `F-02`, `F-03`, and `F-04` in **Section 6: Out of Scope**.

### Step 3: Write the Regression Test & Fix `quota_allocator_fixed.py`
Update `_replenish` so `last_replenished` only advances by `added / self._refill_rate_per_sec` when `added > 0`, preserving fractional elapsed time (`REQ-0005`).

---

## 4. Self-Diagnosis & Grading
Run `./self_diagnose.sh` to verify that the bugged implementation fails the `REQ-0005` test and the fixed implementation passes all `REQ-0001..REQ-0006` tests:

```bash
./self_diagnose.sh
```

---

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Drift Audit & Scoped Track**:
   - Use **plan mode** for the drift audit with `/opsx:explore` and `/opsx:verify` across `specs/spec.md`, `service/quota_allocator.py`, and `scorecard.md`.
   - Run `/conductor:conductor-new-track` with the new track scoped to `F-01` only (`F-02`, `F-03`, and `F-04` in Out of Scope), and save the track specification to `labs/lab_04_drift_detection_and_5step_refactoring/work/spec.md`.
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Clean Implementation Session**: Start a new session (or run `/clear`) before implementing.
5. **Set Goal & Implement**: Set the session goal and run `/conductor:conductor-implement` and `/opsx:apply` to write `test_*.py` and the fixed module under `labs/lab_04_drift_detection_and_5step_refactoring/work/` (leaving `service/quota_allocator.py` unmodified):
   ```text
   /goal ./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh work exits 0, shown by running it; no file under adversarial_tests/ or expected_output/ is modified; or stop after 20 turns.
   ```
6. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh work
   ```
