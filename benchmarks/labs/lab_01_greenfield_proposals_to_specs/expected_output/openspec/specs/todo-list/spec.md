# Capability Specification: `todo-list` (TaskFlow Core To-Do List)

## Purpose
Provides the core in-memory To-Do task list for `TaskFlow`, allowing users to add tasks with auto-incrementing integer IDs, mark tasks complete, filter pending vs. completed tasks, and delete tasks cleanly.

## Requirements

### Requirement: REQ-0001 — Add Task and Reject Blank Titles
The `TodoList.add_task(title)` method SHALL trim leading and trailing whitespace from `title`, assign a sequential integer `id` starting at `1`, initialize `completed` to `False`, and return the created task dictionary. It MUST raise `ValueError` if the trimmed `title` is empty.

#### Scenario: Adding a valid task trims whitespace and assigns sequential ID
- **GIVEN** a new `TodoList` instance
- **WHEN** `add_task("  Buy milk  ")` is called followed by `add_task("Read book")`
- **THEN** the first task returns `{"id": 1, "title": "Buy milk", "completed": False}` and the second returns `{"id": 2, "title": "Read book", "completed": False}`

#### Scenario: Adding an empty or whitespace-only title raises ValueError
- **GIVEN** a `TodoList` instance
- **WHEN** `add_task("   ")` is called
- **THEN** it raises `ValueError` and no task is stored

### Requirement: REQ-0002 — Mark Task Completed
The `TodoList.complete_task(task_id)` method SHALL mark the matching task's `completed` field as `True` and return the updated task dictionary. It MUST raise `KeyError` if `task_id` does not exist.

#### Scenario: Completing an existing task sets completed to True
- **GIVEN** a `TodoList` with task `1` (`"Buy milk"`)
- **WHEN** `complete_task(1)` is called
- **THEN** task `1` has `"completed": True`

#### Scenario: Completing a missing task ID raises KeyError
- **GIVEN** an empty `TodoList`
- **WHEN** `complete_task(99)` is called
- **THEN** it raises `KeyError`

### Requirement: REQ-0003 — Filter Pending and Completed Tasks
The `TodoList.get_pending()` method SHALL return all tasks with `completed == False` in creation order, and `TodoList.get_completed()` SHALL return all tasks with `completed == True` in creation order.

#### Scenario: Pending and completed filters separate tasks accurately
- **GIVEN** a `TodoList` where task `1` is completed and task `2` is still pending
- **WHEN** `get_pending()` and `get_completed()` are called
- **THEN** `get_pending()` returns `[task_2]` and `get_completed()` returns `[task_1]`

### Requirement: REQ-0004 — Delete Task by ID
The `TodoList.delete_task(task_id)` method SHALL remove the task with `task_id` and return `True` if it existed, or return `False` without raising an error if `task_id` was not found.

#### Scenario: Deleting an existing task removes it and returns True
- **GIVEN** a `TodoList` with task `1`
- **WHEN** `delete_task(1)` is called followed by a second `delete_task(1)`
- **THEN** the first call returns `True`, the task is removed, and the second call returns `False`
