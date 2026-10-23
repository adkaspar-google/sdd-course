# Technical Design: TaskFlow Daily Habit Streak Tracker (`habit-tracker`)

## Context
Implements a Duolingo-style daily streak counter (`HabitTracker` in `habit_tracker.py`) using integer day numbers (`day = 1, 2, 3...`) so tests are 100% deterministic without system clock sleeps.

## State Transition Rules on `check_in(name, day)`
1. Validate `name in self._habits` (else `KeyError`) and `day >= 1` (else `ValueError`).
2. If `last_day is None`: set `streak = 1`, `last_day = day`.
3. If `day < last_day`: raise `ValueError("Cannot check in for a past day.")`.
4. If `day == last_day`: keep `streak` unchanged (`REQ-0003` idempotency).
5. If `day == last_day + 1`: increment `streak += 1`, `last_day = day` (`REQ-0002`).
6. If `day > last_day + 1`: reset `streak = 1`, `last_day = day` (`REQ-0004` missed day reset).
