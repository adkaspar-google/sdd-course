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

"""TaskFlow Lab 01: Core To-Do List implementation (REQ-0001..REQ-0004)."""

from __future__ import annotations
from typing import Any


class TodoList:
  """In-memory To-Do list managing tasks with sequential integer IDs."""

  def __init__(self) -> None:
    self._tasks: dict[int, dict[str, Any]] = {}
    self._next_id: int = 1

  def add_task(self, title: str) -> dict[str, Any]:
    """REQ-0001: Add a task with a trimmed title and sequential ID."""
    cleaned = title.strip()
    if not cleaned:
      raise ValueError("Task title must not be empty.")
    task = {"id": self._next_id, "title": cleaned, "completed": False}
    self._tasks[self._next_id] = task
    self._next_id += 1
    return dict(task)

  def complete_task(self, task_id: int) -> dict[str, Any]:
    """REQ-0002: Mark an existing task as completed or raise KeyError."""
    if task_id not in self._tasks:
      raise KeyError(f"Task {task_id} not found.")
    self._tasks[task_id]["completed"] = True
    return dict(self._tasks[task_id])

  def get_pending(self) -> list[dict[str, Any]]:
    """REQ-0003: Return all incomplete tasks in creation order."""
    return [dict(t) for t in self._tasks.values() if not t["completed"]]

  def get_completed(self) -> list[dict[str, Any]]:
    """REQ-0003: Return all completed tasks in creation order."""
    return [dict(t) for t in self._tasks.values() if t["completed"]]

  def delete_task(self, task_id: int) -> bool:
    """REQ-0004: Remove task by ID and return True, or False if missing."""
    if task_id not in self._tasks:
      return False
    del self._tasks[task_id]
    return True
