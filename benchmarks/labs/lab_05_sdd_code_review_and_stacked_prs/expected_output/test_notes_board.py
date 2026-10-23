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

"""Unit tests for TaskFlow Lab 05 NotesBoard (REQ-0001..REQ-0004)."""

import unittest
from notes_board import NotesBoard


class TestNotesBoard(unittest.TestCase):
  """Verifies REQ-0001 through REQ-0004 for NotesBoard."""

  def test_req0001_add_note_trims_text_and_rejects_blank(self) -> None:
    """Verifies REQ-0001: add_note trims text, sets pinned=False, and rejects blank strings."""
    board = NotesBoard()
    n1 = board.add_note("  First note  ")
    self.assertEqual(n1, {"id": 1, "text": "First note", "pinned": False})
    with self.assertRaises(ValueError):
      board.add_note("   ")

  def test_req0002_list_notes_preserves_chronological_creation_order(self) -> None:
    """Verifies REQ-0002: list_notes returns notes in oldest-to-newest creation order."""
    board = NotesBoard()
    board.add_note("Note 1")
    board.add_note("Note 2")
    board.add_note("Note 3")
    self.assertEqual(
        [n["text"] for n in board.list_notes()], ["Note 1", "Note 2", "Note 3"]
    )

  def test_req0003_search_is_case_insensitive_and_delete_removes_note(self) -> None:
    """Verifies REQ-0003: search matches case-insensitively and delete_note removes by ID."""
    board = NotesBoard()
    board.add_note("Call Alice")
    board.add_note("Email Bob")
    self.assertEqual([n["text"] for n in board.search("ALICE")], ["Call Alice"])
    self.assertTrue(board.delete_note(1))
    self.assertFalse(board.delete_note(1))

  def test_req0004_pin_note_and_raise_on_missing_id(self) -> None:
    """Verifies REQ-0004: pin_note marks pinned=True, raises KeyError on missing ID, and filters pinned."""
    board = NotesBoard()
    board.add_note("Regular note")
    board.add_note("Important note")
    pinned = board.pin_note(2)
    self.assertTrue(pinned["pinned"])
    self.assertEqual(
        [n["text"] for n in board.get_pinned_notes()], ["Important note"]
    )
    # Chronological list_notes() order must remain intact
    self.assertEqual(
        [n["text"] for n in board.list_notes()],
        ["Regular note", "Important note"],
    )
    with self.assertRaises(KeyError):
      board.pin_note(99)


if __name__ == "__main__":
  unittest.main()
