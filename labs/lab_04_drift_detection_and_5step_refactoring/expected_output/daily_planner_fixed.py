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

"""TaskFlow Lab 04: Remediated DailyPlanner fixing REQ-0003 exact-budget fit."""

from __future__ import annotations
from typing import Any


class DailyPlanner:
  """Plans daily tasks within a fixed minute budget (REQ-0001..REQ-0004 compliant)."""

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
    """REQ-0002..0004: Schedule a task when used_minutes + minutes <= daily_limit_minutes."""
    cleaned = title.strip()
    if not cleaned:
      raise ValueError("Task title must not be empty.")
    if minutes <= 0:
      raise ValueError("Task minutes must be positive.")

    # FIXED (REQ-0003): Only reject when strictly exceeding daily_limit_minutes (`>`)
    if self.used_minutes + minutes > self.daily_limit_minutes:
      return False

    self.used_minutes += minutes
    self._tasks.append({"title": cleaned, "minutes": minutes})
    return True

  def get_scheduled_tasks(self) -> list[dict[str, Any]]:
    return [dict(t) for t in self._tasks]

  def reset_day(self) -> None:
    self.used_minutes = 0
    self._tasks.clear()
