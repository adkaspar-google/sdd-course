# Capability Specification: `daily-planner` (TaskFlow Daily Time-Budget Planner)

## Purpose
Allows `TaskFlow` users to set a daily focus time budget in minutes (e.g., `120` minutes) and schedule tasks into their day without exceeding their daily limit.

## Requirements

### Requirement: REQ-0001 — Initialize Daily Minute Budget
The `DailyPlanner(daily_limit_minutes=240)` constructor SHALL initialize `used_minutes = 0` and `remaining_minutes = daily_limit_minutes`, and MUST raise `ValueError` if `daily_limit_minutes <= 0`.

#### Scenario: Initializing a 120-minute daily budget starts at 0 used and 120 remaining
- **GIVEN** `planner = DailyPlanner(120)`
- **WHEN** `planner.used_minutes` and `planner.remaining_minutes` are read
- **THEN** `used_minutes` is `0` and `remaining_minutes` is `120`

### Requirement: REQ-0002 — Schedule Task Within Budget
The `DailyPlanner.schedule_task(title, minutes)` method SHALL append the task to the day's schedule, add `minutes` to `used_minutes`, and return `True` when the task fits within the budget.

#### Scenario: Scheduling a 45-minute task updates used and remaining minutes
- **GIVEN** a `DailyPlanner(120)`
- **WHEN** `schedule_task("Write report", 45)` is called
- **THEN** it returns `True`, `used_minutes` is `45`, and `remaining_minutes` is `75`

### Requirement: REQ-0003 — Accept Exact Budget Fit and Reject Over-Budget Tasks
The `DailyPlanner.schedule_task(title, minutes)` method SHALL return `True` whenever `used_minutes + minutes <= daily_limit_minutes` (including when `remaining_minutes` reaches `0` exactly), and SHALL return `False` without modifying state only when `used_minutes + minutes > daily_limit_minutes`.

#### Scenario: Scheduling a task that uses the exact remaining minutes succeeds
- **GIVEN** a `DailyPlanner(120)` with `60` minutes already used (`60` minutes remaining)
- **WHEN** `schedule_task("Deep work session", 60)` is called
- **THEN** it returns `True`, `used_minutes` becomes `120`, and `remaining_minutes` becomes `0`

#### Scenario: Scheduling a task that exceeds remaining minutes returns False
- **GIVEN** a `DailyPlanner(120)` with `90` minutes already used (`30` minutes remaining)
- **WHEN** `schedule_task("Long meeting", 45)` is called
- **THEN** it returns `False` and `used_minutes` remains `90`

### Requirement: REQ-0004 — Validate Task Inputs and Support Daily Reset
The `DailyPlanner.schedule_task(title, minutes)` method MUST raise `ValueError` if `title` is blank or `minutes <= 0`, and `DailyPlanner.reset_day()` SHALL clear all scheduled tasks and reset `used_minutes = 0`.

#### Scenario: Resetting the day clears scheduled tasks and restores full budget
- **GIVEN** a `DailyPlanner(120)` with scheduled tasks
- **WHEN** `reset_day()` is called
- **THEN** `used_minutes` is `0`, `remaining_minutes` is `120`, and `get_scheduled_tasks()` is `[]`
