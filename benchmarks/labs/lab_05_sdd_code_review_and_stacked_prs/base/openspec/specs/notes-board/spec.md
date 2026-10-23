# Capability Specification: `notes-board` (TaskFlow Quick Notes Board — Baseline)

## Purpose
Manages quick text notes inside `TaskFlow` with sequential integer IDs, chronological listing, and case-insensitive keyword search.

## Requirements

### Requirement: REQ-0001 — Add Note and Reject Blank Text
The `NotesBoard.add_note(text)` method SHALL trim `text`, assign a sequential integer `id` starting at `1`, set `pinned = False`, and raise `ValueError` if trimmed `text` is empty.

#### Scenario: Adding a valid note assigns sequential ID
- **GIVEN** a new `NotesBoard`
- **WHEN** `add_note("  Buy domains  ")` is called
- **THEN** it returns `{"id": 1, "text": "Buy domains", "pinned": False}`

### Requirement: REQ-0002 — List Notes in Chronological Creation Order
The `NotesBoard.list_notes()` method SHALL return all stored notes in chronological creation order (`id = 1, 2, 3...`).

#### Scenario: Listing notes preserves oldest-to-newest creation order
- **GIVEN** notes `1` (`"First"`) and `2` (`"Second"`)
- **WHEN** `list_notes()` is called
- **THEN** the returned list has `"First"` followed by `"Second"`

### Requirement: REQ-0003 — Case-Insensitive Keyword Search and Deletion
The `NotesBoard.search(keyword)` method SHALL return notes whose `text` contains `keyword` (case-insensitive) in creation order, and `delete_note(note_id)` SHALL remove the note and return `True` if found or `False` if missing.

#### Scenario: Searching by keyword matches case-insensitively
- **GIVEN** notes `"Call Alice"` and `"Email Bob"`
- **WHEN** `search("alice")` is called
- **THEN** only `"Call Alice"` is returned
