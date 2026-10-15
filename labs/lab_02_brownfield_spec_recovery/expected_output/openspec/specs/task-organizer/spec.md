# Capability Specification: `task-organizer` (TaskFlow Tag & Priority Organizer)

## Purpose
Recovers the formal specification (`Sync Spec`) for the existing brownfield `TaskOrganizer` module (`service/task_organizer.py`), which organizes `TaskFlow` tasks using lowercase-normalized tags and a 3-tier priority ranking (`high`, `medium`, `low`).

## Requirements

### Requirement: REQ-0001 — Lowercase Tag Normalization and Deduplication
The `TaskOrganizer.add_task(title, priority="medium", tags=None)` method SHALL trim and lowercase every tag in `tags`, remove duplicate tags while preserving first-seen order, and raise `ValueError` if `title` or any tag is empty after trimming.

#### Scenario: Mixed-case duplicate tags are normalized to unique lowercase tags
- **GIVEN** a `TaskOrganizer` instance
- **WHEN** `add_task("Prepare slides", tags=["Work", " URGENT ", "work"])` is called
- **THEN** the returned task stores `"tags": ["work", "urgent"]`

### Requirement: REQ-0002 — Three-Tier Priority Level Validation
The `TaskOrganizer.add_task()` method SHALL accept only `"low"`, `"medium"`, or `"high"` for `priority` (defaulting to `"medium"`), and MUST raise `ValueError` for any other priority string.

#### Scenario: Unknown priority level raises ValueError
- **GIVEN** a `TaskOrganizer` instance
- **WHEN** `add_task("Fix outage", priority="urgent")` is called
- **THEN** it raises `ValueError`

### Requirement: REQ-0003 — Case-Insensitive Tag Filtering
The `TaskOrganizer.filter_by_tag(tag)` method SHALL trim and lowercase `tag` and return all matching tasks in chronological creation order.

#### Scenario: Searching with uppercase tag returns matching tasks in creation order
- **GIVEN** tasks tagged with `"home"` and `"Home"`
- **WHEN** `filter_by_tag("  HOME ")` is called
- **THEN** both tasks are returned in creation order

### Requirement: REQ-0004 — Priority-Ordered Task Listing
The `TaskOrganizer.list_by_priority()` method SHALL return all tasks ordered by priority (`"high"` first, `"medium"` second, `"low"` third), using creation order (`id`) as the tie-breaker within the same priority level.

#### Scenario: Tasks sort from high to low while preserving creation order ties
- **GIVEN** tasks added in order: `Low task` (`low`), `High task 1` (`high`), `Medium task` (`medium`), `High task 2` (`high`)
- **WHEN** `list_by_priority()` is called
- **THEN** the titles are returned in order `["High task 1", "High task 2", "Medium task", "Low task"]`
