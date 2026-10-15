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

"""TaskFlow Lab 02: Brownfield Tag & Priority Organizer (REQ-0001..REQ-0004)."""

from __future__ import annotations
from typing import Any

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


class TaskOrganizer:
  """Organizes TaskFlow tasks by normalized lowercase tags and 3-tier priority."""

  def __init__(self) -> None:
    self._tasks: list[dict[str, Any]] = []
    self._next_id: int = 1

  def add_task(
      self,
      title: str,
      priority: str = "medium",
      tags: list[str] | None = None,
  ) -> dict[str, Any]:
    """REQ-0001 & REQ-0002: Validate title/priority and normalize tags to lowercase."""
    cleaned_title = title.strip()
    if not cleaned_title:
      raise ValueError("Task title must not be empty.")
    if priority not in PRIORITY_RANK:
      raise ValueError(f"Invalid priority '{priority}'. Must be low, medium, or high.")

    normalized_tags: list[str] = []
    for raw_tag in tags or []:
      tag = raw_tag.strip().lower()
      if not tag:
        raise ValueError("Tag must not be empty.")
      if tag not in normalized_tags:
        normalized_tags.append(tag)

    task = {
        "id": self._next_id,
        "title": cleaned_title,
        "priority": priority,
        "tags": normalized_tags,
    }
    self._tasks.append(task)
    self._next_id += 1
    return dict(task)

  def filter_by_tag(self, tag: str) -> list[dict[str, Any]]:
    """REQ-0003: Return tasks matching tag (case-insensitive) in creation order."""
    needle = tag.strip().lower()
    return [dict(t) for t in self._tasks if needle in t["tags"]]

  def list_by_priority(self) -> list[dict[str, Any]]:
    """REQ-0004: Return tasks ordered high -> medium -> low, then creation order."""
    ordered = sorted(
        self._tasks, key=lambda t: (PRIORITY_RANK[t["priority"]], t["id"])
    )
    return [dict(t) for t in ordered]
