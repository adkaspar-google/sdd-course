# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for TaskFlow Lab 03 HabitTracker (REQ-0001..REQ-0004)."""

import unittest
from habit_tracker import HabitTracker


class TestHabitTracker(unittest.TestCase):
  """Verifies REQ-0001 through REQ-0004 for HabitTracker."""

  def test_req0001_add_habit_starts_at_zero_and_rejects_blank(self) -> None:
    """Verifies REQ-0001: add_habit trims name, starts at streak 0, and rejects empty names."""
    tracker = HabitTracker()
    record = tracker.add_habit("  Read 20 mins  ")
    self.assertEqual(record, {"name": "Read 20 mins", "streak": 0, "last_day": None})
    self.assertEqual(tracker.get_streak("Read 20 mins"), 0)
    with self.assertRaises(ValueError):
      tracker.add_habit("   ")

  def test_req0002_consecutive_days_increment_streak(self) -> None:
    """Verifies REQ-0002: Consecutive daily check-ins increment streak by 1 each day."""
    tracker = HabitTracker()
    tracker.add_habit("Exercise")
    self.assertEqual(tracker.check_in("Exercise", 1), 1)
    self.assertEqual(tracker.check_in("Exercise", 2), 2)
    self.assertEqual(tracker.check_in("Exercise", 3), 3)

  def test_req0003_same_day_check_in_is_idempotent(self) -> None:
    """Verifies REQ-0003: Checking in multiple times on the same day does not double-count."""
    tracker = HabitTracker()
    tracker.add_habit("Meditate")
    tracker.check_in("Meditate", 1)
    tracker.check_in("Meditate", 2)
    self.assertEqual(tracker.check_in("Meditate", 2), 2)
    self.assertEqual(tracker.get_streak("Meditate"), 2)

  def test_req0004_skipped_day_resets_streak_and_past_day_raises(self) -> None:
    """Verifies REQ-0004: Skipping a day resets streak to 1, and earlier days raise ValueError."""
    tracker = HabitTracker()
    tracker.add_habit("Journal")
    tracker.check_in("Journal", 1)
    tracker.check_in("Journal", 2)
    # Skip Day 3 -> check in on Day 4 resets streak to 1
    self.assertEqual(tracker.check_in("Journal", 4), 1)
    with self.assertRaises(ValueError):
      tracker.check_in("Journal", 3)
    with self.assertRaises(KeyError):
      tracker.check_in("Unknown", 5)


if __name__ == "__main__":
  unittest.main()
