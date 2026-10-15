# Implementation Plan: TaskFlow Core To-Do List (`todo_list_mvp`)

## Phase 1: Specification & Architecture Decisions
- [x] Task 1.1: Run Socratic Clarification ("The Grill") on `proposal.md` to settle blank titles, ID format, and missing-ID semantics.
- [x] Task 1.2: Author `openspec/specs/todo-list/spec.md` (`REQ-0001..REQ-0004`), `ADR-0001-storage-engine.md`, and `ADR-0002-id-assignment.md`.

## Phase 2: Red-Green-Refactor TDD Implementation
- [x] Task 2.1: Write `test_req0001_add_task_and_reject_blank` and implement `add_task`.
- [x] Task 2.2: Write `test_req0002_complete_task` and implement `complete_task`.
- [x] Task 2.3: Write `test_req0003_filter_pending_and_completed` and implement `get_pending` / `get_completed`.
- [x] Task 2.4: Write `test_req0004_delete_task` and implement `delete_task`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Red-Green-Refactor TDD Implementation' [checkpoint: a1b2c3d]
