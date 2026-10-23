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

"""TaskFlow Lab 05: Remediated Quick Notes Board (REQ-0001..REQ-0004)."""

from __future__ import annotations
from typing import Any


class NotesBoard:
  """In-memory quick notes board with chronological ordering and note pinning."""

  def __init__(self) -> None:
    self._notes: dict[int, dict[str, Any]] = {}
    self._next_id: int = 1

  def add_note(self, text: str) -> dict[str, Any]:
    """REQ-0001: Add a note with trimmed text and sequential ID."""
    cleaned = text.strip()
    if not cleaned:
      raise ValueError("Note text must not be empty.")
    note = {"id": self._next_id, "text": cleaned, "pinned": False}
    self._notes[self._next_id] = note
    self._next_id += 1
    return dict(note)

  def list_notes(self) -> list[dict[str, Any]]:
    """REQ-0002: Return all notes in chronological creation order."""
    return [dict(n) for n in self._notes.values()]

  def search(self, keyword: str) -> list[dict[str, Any]]:
    """REQ-0003: Case-insensitive keyword search in creation order."""
    needle = keyword.strip().lower()
    return [
        dict(n) for n in self._notes.values() if needle in n["text"].lower()
    ]

  def delete_note(self, note_id: int) -> bool:
    """REQ-0003: Delete a note by ID and return True, or False if missing."""
    if note_id not in self._notes:
      return False
    del self._notes[note_id]
    return True

  def pin_note(self, note_id: int) -> dict[str, Any]:
    """REQ-0004: Mark an existing note as pinned=True or raise KeyError."""
    if note_id not in self._notes:
      raise KeyError(f"Note {note_id} not found.")
    self._notes[note_id]["pinned"] = True
    return dict(self._notes[note_id])

  def get_pinned_notes(self) -> list[dict[str, Any]]:
    """REQ-0004: Return all pinned notes in chronological creation order."""
    return [dict(n) for n in self._notes.values() if n["pinned"]]
