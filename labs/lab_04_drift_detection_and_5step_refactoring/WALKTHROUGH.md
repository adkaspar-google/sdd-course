# Lab 04 Walkthrough: Spec Drift Detection & 5-Step Brownfield Refactoring (`TaskFlow` Daily Time-Budget Planner)

## 1. Scenario & Why Spec Drift Happens
In **Lab 04**, `TaskFlow` includes a **Daily Time-Budget Planner (`DailyPlanner`)** in [`service/daily_planner.py`](./service/daily_planner.py) governed by [`specs/spec.md`](./specs/spec.md). Users set a daily minute budget (such as `120` minutes) and schedule focus tasks into their day.

Look at **`REQ-0003`** in [`specs/spec.md`](./specs/spec.md):
> *`schedule_task(title, minutes)` SHALL return `True` whenever `used_minutes + minutes <= daily_limit_minutes` (including when `remaining_minutes` reaches `0` exactly).*

Now look at line 45 of [`service/daily_planner.py`](./service/daily_planner.py):
```python
if self.used_minutes + minutes >= self.daily_limit_minutes:
    return False
```
Because the developer wrote `>=` instead of `>`, a user with `60` minutes left in their `120`-minute day who tries to schedule a `60`-minute task gets **`False`**!

---

## 2. Step-by-Step Instructions (The 5-Step Scorecard Refactoring Loop)

### Step 1: Audit Spec vs. Code (`Semantic Diffing`)
Compare [`specs/spec.md`](./specs/spec.md) against [`service/daily_planner.py`](./service/daily_planner.py) and review [`scorecard.md`](./scorecard.md):
- **`F-01` (Critical P0)**: Off-by-one `>=` drift bug violating `REQ-0003`.
- **`F-02`, `F-03`, `F-04` (Low P3)**: Feature ideas (`.ics` export, audio chimes, ANSI colors).

### Step 2: Scope the Track Spec & Lock `F-02..F-04` in `## 6. Out of Scope`
Write `expected_output/spec.md` targeting only **`F-01`** and placing **`F-02`**, **`F-03`**, and **`F-04`** inside `## 6. Out of Scope` (Karpathy's *Surgical Changes* rule).

### Step 3: Write the Failing Regression Test (`Red`) & Surgical Fix (`Green`)
1. Write `test_req0003_exact_remaining_budget_is_accepted_and_over_budget_rejected` in `test_daily_planner.py`.
2. Change `>=` to `>` in `daily_planner_fixed.py`.

### Step 4: Run Differential Self-Diagnosis
```bash
./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh
```
