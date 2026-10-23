# Technical Design: TaskFlow Core To-Do List (`todo-list`)

## Context
`TodoList` is the foundational task storage module in `TaskFlow`.

## Decisions
1. **Storage (`ADR-0001`)**: Use an insertion-ordered `dict[int, dict]` mapping `task_id` to `{"id": int, "title": str, "completed": bool}`.
2. **ID Generation (`ADR-0002`)**: Increment `self._next_id` starting from `1` only after validating that `title.strip()` is non-empty.
3. **Error Handling**:
   - Blank title on `add_task` $\to$ `ValueError`.
   - Unknown `task_id` on `complete_task` $\to$ `KeyError`.
   - Unknown `task_id` on `delete_task` $\to$ returns `False` (idempotent deletion check).
