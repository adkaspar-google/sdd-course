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

"""Read-only adversarial contract tests for Lab 06 TaskFlowBoard (REQ-0001..REQ-0004)."""

import unittest
from taskflow_app import TaskFlowBoard


class TestTaskFlowRebuildContract(unittest.TestCase):
  """Adversarial verification suite for SPEC.md (REQ-0001..REQ-0004)."""

  def test_req0001_add_card_and_validate_inputs(self) -> None:
    """Verifies REQ-0001: add_card trims title, assigns sequential ID, and validates inputs."""
    board = TaskFlowBoard(max_in_progress=2)
    c1 = board.add_card("  Write SPEC.md  ", priority="high", points=3)
    self.assertEqual(
        c1,
        {
            "id": 1,
            "title": "Write SPEC.md",
            "priority": "high",
            "points": 3,
            "status": "todo",
        },
    )
    with self.assertRaises(ValueError):
      board.add_card("   ")
    with self.assertRaises(ValueError):
      board.add_card("Bad priority", priority="urgent")
    with self.assertRaises(ValueError):
      board.add_card("Zero points", points=0)
    with self.assertRaises(ValueError):
      TaskFlowBoard(max_in_progress=0)

  def test_req0002_move_card_and_enforce_wip_limit(self) -> None:
    """Verifies REQ-0002: move_card transitions statuses and enforces max_in_progress."""
    board = TaskFlowBoard(max_in_progress=2)
    board.add_card("Task 1")
    board.add_card("Task 2")
    board.add_card("Task 3")
    board.move_card(1, "in_progress")
    board.move_card(2, "in_progress")
    # 3rd in_progress card must be blocked by WIP limit of 2
    with self.assertRaises(RuntimeError):
      board.move_card(3, "in_progress")
    # Completing Task 1 frees a slot so Task 3 can move to in_progress
    board.move_card(1, "done")
    moved = board.move_card(3, "in_progress")
    self.assertEqual(moved["status"], "in_progress")
    with self.assertRaises(KeyError):
      board.move_card(99, "done")
    with self.assertRaises(ValueError):
      board.move_card(1, "archived")

  def test_req0003_filter_by_status_and_priority(self) -> None:
    """Verifies REQ-0003: get_by_status and get_by_priority filter in creation order."""
    board = TaskFlowBoard(max_in_progress=2)
    board.add_card("Task A", priority="high")
    board.add_card("Task B", priority="low")
    board.add_card("Task C", priority="high")
    board.move_card(2, "done")
    self.assertEqual([c["title"] for c in board.get_by_status("done")], ["Task B"])
    self.assertEqual(
        [c["title"] for c in board.get_by_priority("high")], ["Task A", "Task C"]
    )
    with self.assertRaises(ValueError):
      board.get_by_status("invalid")
    with self.assertRaises(ValueError):
      board.get_by_priority("invalid")

  def test_req0004_board_summary_scorecard_and_completed_points(self) -> None:
    """Verifies REQ-0004: get_summary counts columns and sums points of done cards."""
    board = TaskFlowBoard(max_in_progress=2)
    board.add_card("Card 1", points=3)
    board.add_card("Card 2", points=5)
    board.add_card("Card 3", points=2)
    board.move_card(1, "done")
    board.move_card(2, "in_progress")
    self.assertEqual(
        board.get_summary(),
        {
            "total": 3,
            "todo": 1,
            "in_progress": 1,
            "done": 1,
            "completed_points": 3,
        },
    )


if __name__ == "__main__":
  unittest.main()
