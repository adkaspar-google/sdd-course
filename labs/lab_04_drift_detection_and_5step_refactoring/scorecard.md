# Brownfield Audit Scorecard: TaskFlow `DailyPlanner` (`service/daily_planner.py`)

| Finding ID | Severity | Category | Description | Action Decision |
| :--- | :--- | :--- | :--- | :--- |
| **`F-01`** | **P0 Critical** | **Spec Drift (`REQ-0003`)** | `schedule_task()` uses `if self.used_minutes + minutes >= self.daily_limit_minutes: return False` instead of `>`, rejecting tasks that use 100% of the exact remaining budget (e.g., scheduling a `60`-min task when `60` mins remain). | **FIX NOW** in Track `daily_planner_exact_fit_fix` |
| **`F-02`** | **P3 Low** | Feature Wish | Add `.ics` Google Calendar file export. | **DEFER (`Out of Scope`)** |
| **`F-03`** | **P3 Low** | Feature Wish | Add desktop audio chime when a scheduled task finishes. | **DEFER (`Out of Scope`)** |
| **`F-04`** | **P3 Low** | Cosmetic | Add ANSI terminal color themes for remaining budget bars. | **DEFER (`Out of Scope`)** |
