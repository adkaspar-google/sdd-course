# Track Specification: TaskFlow Core To-Do List (`todo_list_mvp`)

## 1. Overview
Implement the greenfield `TodoList` component (`todo_list.py`) for `TaskFlow`, turning the informal product proposal into a verified, 4-requirement capability contract (`REQ-0001..REQ-0004`).

## 2. Architecture & Component Topology
- **Component**: `TodoList` class in `todo_list.py`.
- **Storage**: In-memory Python `dict[int, dict]` preserving insertion order (`ADR-0001`).
- **Identity**: Auto-incrementing integer IDs starting at `1` (`ADR-0002`).

## 3. Functional Requirements
- **REQ-0001**: `add_task(title)` trims whitespace, assigns sequential `id` (`1, 2, ...`), sets `completed=False`, and raises `ValueError` on empty titles.
- **REQ-0002**: `complete_task(task_id)` sets `completed=True` and returns the task dict, or raises `KeyError` if `task_id` is missing.
- **REQ-0003**: `get_pending()` returns incomplete tasks in creation order; `get_completed()` returns completed tasks in creation order.
- **REQ-0004**: `delete_task(task_id)` deletes the task and returns `True` if found, or `False` if missing.

## 4. Non-Functional Requirements
- Zero external dependencies (Python 3.11+ standard library only).
- $O(1)$ lookup for `complete_task` and `delete_task` by `task_id`.

## 5. Acceptance Criteria
- [x] `openspec/specs/todo-list/spec.md` defines `REQ-0001` through `REQ-0004` with `#### Scenario:` blocks.
- [x] `ADR-0001-storage-engine.md` and `ADR-0002-id-assignment.md` document key design choices.
- [x] All 4 unit tests (`test_req0001_*` through `test_req0004_*`) pass.

## 6. Out of Scope
- Tags and priority levels (deferred to Lab 02 `task_organizer.py`).
- Daily habit streaks (deferred to Lab 03 `habit_tracker.py`).

## 7. Verification Commands
```bash
CI=true python3 -m unittest discover -s labs/lab_01_greenfield_proposals_to_specs/expected_output -p "test_*.py" -v
./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh
```
