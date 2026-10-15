# ADR-0001: In-Memory Dictionary Keyed by Task ID

- **Status**: Accepted
- **Context**: `TaskFlow` needs a clean storage structure for tasks that preserves creation order while supporting fast lookup and deletion by `task_id`.
- **Decision**: Store tasks in a Python `dict[int, dict]` (`self._tasks[task_id] = task`). Since Python 3.7+, `dict` preserves insertion order natively while giving $O(1)$ lookup and deletion by `task_id`.
- **Consequences**: `complete_task(task_id)` and `delete_task(task_id)` execute in $O(1)$ time, and `get_pending()` / `get_completed()` iterate in creation order without needing a separate list index.
