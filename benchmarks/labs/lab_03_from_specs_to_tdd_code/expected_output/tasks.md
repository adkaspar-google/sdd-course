# Tasks: TaskFlow Daily Habit Streak Tracker (`habit-tracker`)

## Batch 1: Habit Registration & Consecutive Check-Ins (`REQ-0001..REQ-0002`)
- [x] 1.1 Write `test_req0001_add_habit_starts_at_zero_and_rejects_blank` in `test_habit_tracker.py` and implement `add_habit` / `get_streak` in `habit_tracker.py`.
- [x] 1.2 Write `test_req0002_consecutive_days_increment_streak` and implement consecutive-day increment in `check_in`.

## Batch 2: Idempotency & Skipped-Day Reset (`REQ-0003..REQ-0004`)
- [x] 2.1 Write `test_req0003_same_day_check_in_is_idempotent` and handle `day == last_day`.
- [x] 2.2 Write `test_req0004_skipped_day_resets_streak_and_past_day_raises` and handle `day > last_day + 1` reset and `day < last_day` validation.
