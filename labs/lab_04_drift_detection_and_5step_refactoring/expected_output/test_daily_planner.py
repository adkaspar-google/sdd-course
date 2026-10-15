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

"""Unit tests for TaskFlow Lab 04 DailyPlanner (REQ-0001..REQ-0004)."""

import unittest
from daily_planner_fixed import DailyPlanner


class TestDailyPlanner(unittest.TestCase):
  """Verifies REQ-0001 through REQ-0004 for DailyPlanner."""

  def test_req0001_initialize_daily_budget_and_reject_non_positive(self) -> None:
    """Verifies REQ-0001: DailyPlanner starts with 0 used minutes and rejects <= 0 limits."""
    planner = DailyPlanner(120)
    self.assertEqual(planner.used_minutes, 0)
    self.assertEqual(planner.remaining_minutes, 120)
    with self.assertRaises(ValueError):
      DailyPlanner(0)

  def test_req0002_schedule_task_within_budget_updates_used_minutes(self) -> None:
    """Verifies REQ-0002: Scheduling a task within budget increments used_minutes."""
    planner = DailyPlanner(120)
    self.assertTrue(planner.schedule_task("Write spec", 45))
    self.assertEqual(planner.used_minutes, 45)
    self.assertEqual(planner.remaining_minutes, 75)

  def test_req0003_exact_remaining_budget_is_accepted_and_over_budget_rejected(self) -> None:
    """Verifies REQ-0003: Exact budget fit (remaining == 0) succeeds; exceeding budget returns False."""
    planner = DailyPlanner(120)
    self.assertTrue(planner.schedule_task("Morning block", 60))
    # Scheduling a 60-minute task when 60 minutes remain MUST succeed (F-01 regression test)
    self.assertTrue(planner.schedule_task("Afternoon block", 60))
    self.assertEqual(planner.used_minutes, 120)
    self.assertEqual(planner.remaining_minutes, 0)
    # Any additional task over 120 minutes MUST return False without changing used_minutes
    self.assertFalse(planner.schedule_task("Extra task", 15))
    self.assertEqual(planner.used_minutes, 120)

  def test_req0004_validate_inputs_and_reset_day(self) -> None:
    """Verifies REQ-0004: Blank titles or <= 0 minutes raise ValueError, and reset_day clears state."""
    planner = DailyPlanner(120)
    with self.assertRaises(ValueError):
      planner.schedule_task("   ", 30)
    with self.assertRaises(ValueError):
      planner.schedule_task("Valid title", 0)
    planner.schedule_task("Focus block", 50)
    planner.reset_day()
    self.assertEqual(planner.used_minutes, 0)
    self.assertEqual(planner.get_scheduled_tasks(), [])


if __name__ == "__main__":
  unittest.main()
