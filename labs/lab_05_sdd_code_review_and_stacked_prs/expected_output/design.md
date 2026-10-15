# Technical Design: TaskFlow Quick Notes Board Pinning (`notes-board`)

## Context
Remediates the three SDD review findings from `simulated_review/subpar_change.patch`.

## Decisions
1. **Preserve `REQ-0002` Creation Order**: `list_notes()` MUST iterate `self._notes.values()` in insertion order without `reversed(...)`.
2. **Synchronize `REQ-0004` (`Sync Spec`)**: Document `pin_note(note_id)` and `get_pinned_notes()` in `openspec/specs/notes-board/spec.md` before merging code.
3. **Fail Fast on Unknown IDs**: `pin_note(note_id)` raises `KeyError` when `note_id not in self._notes`.
