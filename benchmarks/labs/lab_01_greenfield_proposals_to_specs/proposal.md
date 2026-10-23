# Proposal: TaskFlow Core To-Do List (`todo-list`)

## Why
We are launching **TaskFlow**, a simple personal productivity app. For our first release, users need a fast, reliable **To-Do List** where they can add tasks, mark tasks as completed, filter their pending vs. completed tasks, and delete tasks they no longer need.

## What Changes
Build the core `TodoList` Python class (`todo_list.py`) supporting four operations:
1. `add_task(title)` — add a new task and return its record.
2. `complete_task(task_id)` — mark a task as completed.
3. `get_pending()` and `get_completed()` — list incomplete vs. completed tasks.
4. `delete_task(task_id)` — remove a task by ID.

## Open Questions for Interactive Socratic Grilling ("The Grill")
Before generating specifications or code, resolve these 3 edge cases:
- **Q1 (Blank Titles)**: What should happen if a user calls `add_task("")` or `add_task("   ")`?
- **Q2 (ID Format)**: Should task IDs be 36-character UUID strings or sequential integers (`1, 2, 3...`)?
- **Q3 (Missing IDs)**: How should `complete_task(task_id)` vs. `delete_task(task_id)` behave when given an ID that does not exist?

## Capabilities
- **New Capabilities**: `todo-list`
- **Modified Capabilities**: None (Greenfield)

## Impact
- Pure Python 3.11+ standard library (`todo_list.py` + `test_todo_list.py`).
