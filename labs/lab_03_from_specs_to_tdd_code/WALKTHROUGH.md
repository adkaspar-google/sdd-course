# Lab 03: From Specs to TDD Code — Implementing a Circuit Breaker State Machine

**Estimated Time**: 40–50 minutes  
**Frameworks Practiced**: Conductor (`/conductor:implement` Red-Green-Refactor TDD) + OpenSpec (`/opsx:apply`) + 1:1 `REQ-XXXX` Test Traceability

---

## 1. Learning Objective
In this hands-on lab, you start with a finalized behavioral specification (`specs/spec.md`) and technical design (`specs/design.md`) for a **Circuit Breaker with Half-Open Recovery**. Your goal is to translate `REQ-0001` through `REQ-0007` into a sequenced TDD task breakdown (`tasks.md`), write traceable unit tests (`test_req0001_...` through `test_req0007_...`), and implement the state machine (`circuitbreaker.py`).

---

## 2. Starting Input
Inspect [`specs/spec.md`](./specs/spec.md) and [`specs/design.md`](./specs/design.md):
- `REQ-0001`: Initial `CLOSED` state forwards calls and returns results.
- `REQ-0002`: Consecutive failures reaching `failure_threshold` trip the breaker from `CLOSED` to `OPEN`.
- `REQ-0003`: While `OPEN` (before `recovery_timeout_seconds` elapses), calls fail fast with `CircuitOpenError` without invoking the wrapped callable.
- `REQ-0004`: Once `recovery_timeout_seconds` elapses, the breaker transitions to `HALF_OPEN` and permits at most `half_open_max_calls=1` probe call.
- `REQ-0005`: A successful probe call in `HALF_OPEN` resets consecutive failures to `0` and transitions back to `CLOSED`.
- `REQ-0006`: A failed probe call in `HALF_OPEN` immediately re-opens the circuit (`OPEN`) and resets the recovery timer.
- `REQ-0007`: A successful call in `CLOSED` resets any prior consecutive failure count below threshold back to `0`.

---

## 3. Hands-On Exercise Steps

### Step 1: Decompose Requirements into TDD Tasks (`tasks.md`)
Map each requirement to a Red-Green-Refactor task and organize them into logical implementation batches.

### Step 2: Execute Red-Green-Refactor (`/conductor:implement`)
1. Write `test_req0001_...` through `test_req0007_...` in `test_circuitbreaker.py`.
2. Implement `CircuitState`, `CircuitOpenError`, and `CircuitBreaker` in `circuitbreaker.py`.

---

## 4. Self-Diagnosis & Grading
Run the automated diagnostic script to execute the unit test suite and verify 100% requirement-to-test traceability:

```bash
./self_diagnose.sh
```

---

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Plan the Track**: Inspect `labs/lab_03_from_specs_to_tdd_code/specs/spec.md` and `specs/design.md` in **plan mode**, then run `/conductor:conductor-new-track` and `/opsx:propose` to prepare the phased TDD plan.
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Clean Implementation Session**: Start a new session (or run `/clear`) before implementing so implementation begins with clean context.
5. **Set Goal & Implement**: Set the session goal and run `/conductor:conductor-implement` and `/opsx:apply` to write `test_circuitbreaker.py` and `circuitbreaker.py` in `labs/lab_03_from_specs_to_tdd_code/work/`:
   ```text
   /goal ./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh work exits 0, shown by running it; no file under adversarial_tests/ or expected_output/ is modified; or stop after 20 turns.
   ```
6. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh work
   ```
