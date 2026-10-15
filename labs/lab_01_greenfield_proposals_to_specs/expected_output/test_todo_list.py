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

"""Unit tests for TaskFlow Lab 01 TodoList (REQ-0001..REQ-0004)."""

import unittest
from todo_list import TodoList


class TestTodoList(unittest.TestCase):
  """Verifies REQ-0001 through REQ-0004 for TodoList."""

  def test_req0001_add_task_trims_title_and_rejects_blank(self) -> None:
    """Verifies REQ-0001: add_task trims whitespace, assigns sequential IDs, and rejects blank titles."""
    todos = TodoList()
    t1 = todos.add_task("  Buy groceries  ")
    t2 = todos.add_task("Write spec")
    self.assertEqual(t1, {"id": 1, "title": "Buy groceries", "completed": False})
    self.assertEqual(t2, {"id": 2, "title": "Write spec", "completed": False})
    with self.assertRaises(ValueError):
      todos.add_task("   ")

  def test_req0002_complete_task_marks_done_and_raises_on_missing_id(self) -> None:
    """Verifies REQ-0002: complete_task sets completed=True and raises KeyError when missing."""
    todos = TodoList()
    todos.add_task("Buy groceries")
    updated = todos.complete_task(1)
    self.assertTrue(updated["completed"])
    with self.assertRaises(KeyError):
      todos.complete_task(99)

  def test_req0003_filter_pending_and_completed_preserves_order(self) -> None:
    """Verifies REQ-0003: get_pending and get_completed separate tasks in creation order."""
    todos = TodoList()
    todos.add_task("Task A")
    todos.add_task("Task B")
    todos.add_task("Task C")
    todos.complete_task(2)
    self.assertEqual([t["title"] for t in todos.get_pending()], ["Task A", "Task C"])
    self.assertEqual([t["title"] for t in todos.get_completed()], ["Task B"])

  def test_req0004_delete_task_returns_boolean_status(self) -> None:
    """Verifies REQ-0004: delete_task removes existing task and returns False if not found."""
    todos = TodoList()
    todos.add_task("Temporary task")
    self.assertTrue(todos.delete_task(1))
    self.assertFalse(todos.delete_task(1))
    self.assertEqual(todos.get_pending(), [])


if __name__ == "__main__":
  unittest.main()
