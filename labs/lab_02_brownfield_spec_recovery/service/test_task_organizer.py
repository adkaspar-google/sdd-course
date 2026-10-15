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

"""Unit tests for TaskFlow Lab 02 TaskOrganizer (REQ-0001..REQ-0004)."""

import unittest
from task_organizer import TaskOrganizer


class TestTaskOrganizer(unittest.TestCase):
  """Verifies REQ-0001 through REQ-0004 for TaskOrganizer."""

  def test_req0001_normalize_and_deduplicate_tags_lowercase(self) -> None:
    """Verifies REQ-0001: Tags are trimmed, lowercased, deduplicated, and blank tags rejected."""
    org = TaskOrganizer()
    task = org.add_task("Prepare slides", tags=["Work", " URGENT ", "work"])
    self.assertEqual(task["tags"], ["work", "urgent"])
    with self.assertRaises(ValueError):
      org.add_task("Bad tag", tags=["   "])

  def test_req0002_validate_priority_levels(self) -> None:
    """Verifies REQ-0002: Priority must be low, medium, or high."""
    org = TaskOrganizer()
    default_task = org.add_task("Default priority task")
    self.assertEqual(default_task["priority"], "medium")
    with self.assertRaises(ValueError):
      org.add_task("Invalid priority", priority="critical")

  def test_req0003_filter_by_tag_is_case_insensitive(self) -> None:
    """Verifies REQ-0003: filter_by_tag matches case-insensitively in creation order."""
    org = TaskOrganizer()
    org.add_task("Buy milk", tags=["home"])
    org.add_task("Fix bug", tags=["work"])
    org.add_task("Clean kitchen", tags=["Home"])
    matches = org.filter_by_tag("  HOME ")
    self.assertEqual([t["title"] for t in matches], ["Buy milk", "Clean kitchen"])

  def test_req0004_list_by_priority_orders_high_medium_low(self) -> None:
    """Verifies REQ-0004: list_by_priority orders high -> medium -> low and keeps creation order ties."""
    org = TaskOrganizer()
    org.add_task("Low task", priority="low")
    org.add_task("High task 1", priority="high")
    org.add_task("Medium task", priority="medium")
    org.add_task("High task 2", priority="high")
    ordered = org.list_by_priority()
    self.assertEqual(
        [t["title"] for t in ordered],
        ["High task 1", "High task 2", "Medium task", "Low task"],
    )


if __name__ == "__main__":
  unittest.main()
