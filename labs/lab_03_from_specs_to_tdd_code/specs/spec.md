# Capability Specification: `habit-tracker` (TaskFlow Daily Habit Streak Tracker)

## Purpose
Allows `TaskFlow` users to build daily habits (`"Drink water"`, `"Read 20 mins"`) and track consecutive daily check-in streaks using simple integer day numbers (`Day 1`, `Day 2`, `Day 3...`).

## Requirements

### Requirement: REQ-0001 — Register Habit at Zero Streak
The `HabitTracker.add_habit(name)` method SHALL trim `name`, initialize the habit with `streak = 0` and `last_day = None`, and MUST raise `ValueError` if the trimmed `name` is empty.

#### Scenario: Creating a valid habit starts streak at 0
- **GIVEN** a new `HabitTracker`
- **WHEN** `add_habit("  Read 20 mins  ")` is called
- **THEN** `get_streak("Read 20 mins")` returns `0`

### Requirement: REQ-0002 — Consecutive-Day Check-In Increments Streak
The `HabitTracker.check_in(name, day)` method SHALL set `streak = 1` on the first check-in (`last_day is None`), and SHALL increment `streak` by `1` whenever `day == last_day + 1`.

#### Scenario: Checking in on Day 1, Day 2, and Day 3 builds a streak of 3
- **GIVEN** a registered habit `"Exercise"`
- **WHEN** `check_in("Exercise", 1)`, `check_in("Exercise", 2)`, and `check_in("Exercise", 3)` are called
- **THEN** the streak advances from `1` to `2` to `3`

### Requirement: REQ-0003 — Same-Day Duplicate Check-In Is Idempotent
When `HabitTracker.check_in(name, day)` is called with `day == last_day`, it SHALL leave `streak` and `last_day` unchanged and return the current `streak`.

#### Scenario: Checking in twice on Day 2 does not double-count
- **GIVEN** `"Exercise"` checked in on Day `1` and Day `2` (`streak == 2`)
- **WHEN** `check_in("Exercise", 2)` is called a second time
- **THEN** `streak` remains `2`

### Requirement: REQ-0004 — Skipped Day Resets Streak to 1 and Past Day Raises Error
When `HabitTracker.check_in(name, day)` is called with `day > last_day + 1` (at least one day was skipped), it SHALL reset `streak` to `1` and update `last_day = day`. If `day < last_day` (or `day <= 0`), it MUST raise `ValueError`. If `name` is not registered, it MUST raise `KeyError`.

#### Scenario: Skipping Day 3 and checking in on Day 4 resets streak to 1
- **GIVEN** `"Exercise"` checked in on Day `1` and Day `2` (`streak == 2`)
- **WHEN** Day `3` is skipped and `check_in("Exercise", 4)` is called
- **THEN** `streak` resets to `1` and `last_day` becomes `4`
