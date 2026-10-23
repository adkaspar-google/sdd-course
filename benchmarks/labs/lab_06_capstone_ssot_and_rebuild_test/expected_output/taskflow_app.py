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

"""TaskFlow Lab 06 Capstone: Clean-room rebuild of TaskFlowBoard from SPEC.md."""

from __future__ import annotations
from typing import Any

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"todo", "in_progress", "done"}


class TaskFlowBoard:
  """Unified Kanban board rebuilt from SPEC.md (REQ-0001..REQ-0004)."""

  def __init__(self, max_in_progress: int = 3) -> None:
    if max_in_progress <= 0:
      raise ValueError("max_in_progress must be positive.")
    self.max_in_progress: int = max_in_progress
    self._cards: dict[int, dict[str, Any]] = {}
    self._next_id: int = 1

  def add_card(
      self, title: str, priority: str = "medium", points: int = 1
  ) -> dict[str, Any]:
    """REQ-0001: Create a card in 'todo' status with validated priority and points."""
    cleaned = title.strip()
    if not cleaned:
      raise ValueError("Card title must not be empty.")
    if priority not in VALID_PRIORITIES:
      raise ValueError(f"Invalid priority '{priority}'.")
    if points <= 0:
      raise ValueError("Story points must be a positive integer.")

    card = {
        "id": self._next_id,
        "title": cleaned,
        "priority": priority,
        "points": points,
        "status": "todo",
    }
    self._cards[self._next_id] = card
    self._next_id += 1
    return dict(card)

  def move_card(self, card_id: int, new_status: str) -> dict[str, Any]:
    """REQ-0002: Move card across columns while enforcing max_in_progress."""
    if card_id not in self._cards:
      raise KeyError(f"Card {card_id} not found.")
    if new_status not in VALID_STATUSES:
      raise ValueError(f"Invalid status '{new_status}'.")

    card = self._cards[card_id]
    if new_status == "in_progress" and card["status"] != "in_progress":
      current_wip = sum(
          1 for c in self._cards.values() if c["status"] == "in_progress"
      )
      if current_wip >= self.max_in_progress:
        raise RuntimeError("WIP limit reached for 'in_progress' column.")

    card["status"] = new_status
    return dict(card)

  def get_by_status(self, status: str) -> list[dict[str, Any]]:
    """REQ-0003: Return cards matching status in creation order."""
    if status not in VALID_STATUSES:
      raise ValueError(f"Invalid status '{status}'.")
    return [dict(c) for c in self._cards.values() if c["status"] == status]

  def get_by_priority(self, priority: str) -> list[dict[str, Any]]:
    """REQ-0003: Return cards matching priority in creation order."""
    if priority not in VALID_PRIORITIES:
      raise ValueError(f"Invalid priority '{priority}'.")
    return [dict(c) for c in self._cards.values() if c["priority"] == priority]

  def get_summary(self) -> dict[str, int]:
    """REQ-0004: Return board counts and completed story points."""
    todo = sum(1 for c in self._cards.values() if c["status"] == "todo")
    in_prog = sum(
        1 for c in self._cards.values() if c["status"] == "in_progress"
    )
    done = sum(1 for c in self._cards.values() if c["status"] == "done")
    completed_points = sum(
        c["points"] for c in self._cards.values() if c["status"] == "done"
    )
    return {
        "total": len(self._cards),
        "todo": todo,
        "in_progress": in_prog,
        "done": done,
        "completed_points": completed_points,
    }
