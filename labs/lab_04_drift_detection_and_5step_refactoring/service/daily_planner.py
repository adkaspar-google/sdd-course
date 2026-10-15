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

"""TaskFlow Lab 04: Bugged DailyPlanner service exhibiting REQ-0003 drift."""

from __future__ import annotations
from typing import Any


class DailyPlanner:
  """Plans daily tasks within a fixed minute budget (contains REQ-0003 drift bug)."""

  def __init__(self, daily_limit_minutes: int = 240) -> None:
    if daily_limit_minutes <= 0:
      raise ValueError("daily_limit_minutes must be positive.")
    self.daily_limit_minutes: int = daily_limit_minutes
    self.used_minutes: int = 0
    self._tasks: list[dict[str, Any]] = []

  @property
  def remaining_minutes(self) -> int:
    return self.daily_limit_minutes - self.used_minutes

  def schedule_task(self, title: str, minutes: int) -> bool:
    """Schedule a task if it fits within the daily minute budget."""
    cleaned = title.strip()
    if not cleaned:
      raise ValueError("Task title must not be empty.")
    if minutes <= 0:
      raise ValueError("Task minutes must be positive.")

    # DRIFT BUG AGAINST REQ-0003:
    # Uses `>=` instead of `>`, falsely rejecting a task that uses the exact remaining budget!
    if self.used_minutes + minutes >= self.daily_limit_minutes:
      return False

    self.used_minutes += minutes
    self._tasks.append({"title": cleaned, "minutes": minutes})
    return True

  def get_scheduled_tasks(self) -> list[dict[str, Any]]:
    return [dict(t) for t in self._tasks]

  def reset_day(self) -> None:
    self.used_minutes = 0
    self._tasks.clear()
