# Track Specification: Fix `REQ-0003` Exact-Budget Boundary Drift (`daily_planner_exact_fit_fix`)

## 1. Overview
Remediate finding **`F-01`** from `scorecard.md` where `service/daily_planner.py` drifts from `REQ-0003` by rejecting tasks that use the exact remaining daily budget (`used_minutes + minutes == daily_limit_minutes`).

## 2. Architecture & Component Topology
- **Target Component**: `DailyPlanner.schedule_task()` in `daily_planner_fixed.py`.
- **Root Cause**: Off-by-one comparison operator `>=` instead of `>` when checking `self.used_minutes + minutes` against `self.daily_limit_minutes`.

## 3. Functional Requirements
- **REQ-0001**: Initialize `DailyPlanner(daily_limit_minutes)` with `used_minutes = 0` and reject `daily_limit_minutes <= 0`.
- **REQ-0002**: Schedule tasks that fit within the budget and increment `used_minutes`.
- **REQ-0003**: Accept tasks when `used_minutes + minutes <= daily_limit_minutes` (exact budget fit) and return `False` only when `used_minutes + minutes > daily_limit_minutes`.
- **REQ-0004**: Raise `ValueError` on blank `title` or `minutes <= 0`, and reset state in `reset_day()`.

## 4. Non-Functional Requirements
- **Surgical Changes**: Modify only the boundary check in `schedule_task()` and add the regression test for `REQ-0003`.

## 5. Acceptance Criteria
- [x] `test_req0003_exact_remaining_budget_is_accepted` fails on `service/daily_planner.py` and passes on `expected_output/daily_planner_fixed.py`.
- [x] All 4 requirement tests (`test_req0001_*` through `test_req0004_*`) pass.

## 6. Out of Scope
The following non-critical findings from `scorecard.md` are explicitly locked out of scope to prevent scope creep:
- **F-02**: `.ics` calendar export.
- **F-03**: Desktop audio chimes.
- **F-04**: ANSI terminal color themes.

## 7. Verification Commands
```bash
CI=true python3 -m unittest discover -s labs/lab_04_drift_detection_and_5step_refactoring/expected_output -p "test_*.py" -v
./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh
```
