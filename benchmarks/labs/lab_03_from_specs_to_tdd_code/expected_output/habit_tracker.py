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

"""TaskFlow Lab 03: Daily Habit Streak Tracker (REQ-0001..REQ-0004)."""

from __future__ import annotations
from typing import Any


class HabitTracker:
  """Tracks daily habit check-ins and consecutive-day streaks."""

  def __init__(self) -> None:
    self._habits: dict[str, dict[str, Any]] = {}

  def add_habit(self, name: str) -> dict[str, Any]:
    """REQ-0001: Register a new habit starting at streak=0 and last_day=None."""
    cleaned = name.strip()
    if not cleaned:
      raise ValueError("Habit name must not be empty.")
    record = {"name": cleaned, "streak": 0, "last_day": None}
    self._habits[cleaned] = record
    return dict(record)

  def get_streak(self, name: str) -> int:
    """Return the current streak for a registered habit or raise KeyError."""
    if name not in self._habits:
      raise KeyError(f"Habit '{name}' not found.")
    return int(self._habits[name]["streak"])

  def check_in(self, name: str, day: int) -> int:
    """REQ-0002..0004: Record a check-in on integer day >= 1 and return new streak."""
    if name not in self._habits:
      raise KeyError(f"Habit '{name}' not found.")
    if day <= 0:
      raise ValueError("Day number must be a positive integer >= 1.")

    habit = self._habits[name]
    last_day = habit["last_day"]

    if last_day is None:
      habit["streak"] = 1
      habit["last_day"] = day
    elif day < last_day:
      raise ValueError("Cannot check in on a day earlier than last_day.")
    elif day == last_day:
      # REQ-0003: Same-day check-in is idempotent
      pass
    elif day == last_day + 1:
      # REQ-0002: Consecutive day increments streak
      habit["streak"] += 1
      habit["last_day"] = day
    else:
      # REQ-0004: Skipped day resets streak to 1
      habit["streak"] = 1
      habit["last_day"] = day

    return int(habit["streak"])
