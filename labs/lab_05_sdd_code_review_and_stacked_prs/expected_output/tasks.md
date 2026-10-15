# Stacked PR Task Decomposition: TaskFlow Note Pinning (`add-note-pinning`)

## Batch 1 (PR 1): Spec Delta & Baseline Preservation (`REQ-0001..REQ-0003`)
- [x] 1.1 Add `REQ-0004` (`Pin Note and List Pinned Notes`) to the OpenSpec delta and verify `REQ-0001..REQ-0003` tests pass with chronological `list_notes()` order intact.

## Batch 2 (PR 2): Note Pinning Implementation & Unit Tests (`REQ-0004`)
- [x] 2.1 Implement `pin_note(note_id)` (raising `KeyError` on missing IDs) and `get_pinned_notes()` in `notes_board.py`, verified by `test_req0004_pin_note_and_raise_on_missing_id`.

## Archive PR N+1 (Final Spec Sync & Clean)
- [x] 3.1 Run `/opsx:verify` and `/opsx:archive` in dedicated **Archive PR N+1** to merge `REQ-0004` into `openspec/specs/notes-board/spec.md`.
