# Canonical Specification (`SPEC.md` — Single Source of Truth): `TaskFlowBoard`

## 1. Domain Intent & Business Capabilities
`TaskFlowBoard` (`taskflow_app.py`) is the unified Kanban board for **TaskFlow**. It tracks task cards across three workflow columns (`"todo"`, `"in_progress"`, `"done"`), enforces a Work-In-Progress (`max_in_progress`) limit on `"in_progress"` cards so users do not overload themselves, and calculates a summary scorecard including total completed story points.

## 2. Architecture & Component Topology
- **Module**: `taskflow_app.py` exporting `TaskFlowBoard`.
- **Constructor**: `TaskFlowBoard(max_in_progress: int = 3)` (raises `ValueError` if `max_in_progress <= 0`).

## 3. Data Model & Schemas
Each card dictionary stored in `TaskFlowBoard` has the exact schema:
```python
{
    "id": int,          # Sequential integer starting at 1
    "title": str,       # Non-empty trimmed string
    "priority": str,    # One of {"low", "medium", "high"}
    "points": int,      # Positive integer >= 1
    "status": str,      # One of {"todo", "in_progress", "done"}, starts at "todo"
}
```

## 4. API & Method Contracts (`REQ-0001..REQ-0004`)

### `REQ-0001`: Create Card with Priority and Story Points
- **Signature**: `add_card(title: str, priority: str = "medium", points: int = 1) -> dict[str, Any]`
- **Contract**: SHALL trim `title`, assign sequential integer `id` (`1, 2, ...`), set `status = "todo"`, and return a copy of the card dictionary. MUST raise `ValueError` if trimmed `title` is empty, `priority` is not in `{"low", "medium", "high"}`, or `points <= 0`.

### `REQ-0002`: Move Card Across Columns with Work-In-Progress (`WIP`) Limit
- **Signature**: `move_card(card_id: int, new_status: str) -> dict[str, Any]`
- **Contract**:
  - MUST raise `KeyError` if `card_id` does not exist.
  - MUST raise `ValueError` if `new_status` is not in `{"todo", "in_progress", "done"}`.
  - If `new_status == "in_progress"` and the card is not already `"in_progress"`, and the current count of `"in_progress"` cards is already `>= self.max_in_progress`, it MUST raise `RuntimeError` without changing the card's status.
  - Otherwise, SHALL update `card["status"] = new_status` and return a copy of the updated card.

### `REQ-0003`: Filter Cards by Column Status or Priority
- **Signatures**:
  - `get_by_status(status: str) -> list[dict[str, Any]]` (raises `ValueError` if `status` not in `{"todo", "in_progress", "done"}`)
  - `get_by_priority(priority: str) -> list[dict[str, Any]]` (raises `ValueError` if `priority` not in `{"low", "medium", "high"}`)
- **Contract**: SHALL return matching card dictionaries in creation order (`id = 1, 2, ...`).

### `REQ-0004`: Board Summary Scorecard
- **Signature**: `get_summary() -> dict[str, int]`
- **Contract**: SHALL return a dictionary with exact keys:
  ```python
  {
      "total": int,             # Total cards on board
      "todo": int,              # Count of cards with status == "todo"
      "in_progress": int,       # Count of cards with status == "in_progress"
      "done": int,              # Count of cards with status == "done"
      "completed_points": int,  # Sum of `points` for all cards with status == "done"
  }
  ```

## 5. Core Workflows
1. Cards always start in `"todo"` (`REQ-0001`).
2. Moving a card into `"in_progress"` checks the WIP limit (`REQ-0002`); moving a card to `"done"` frees up an `"in_progress"` slot and adds its `points` to `completed_points` (`REQ-0004`).

## 6. Repository & Directory Structure
```text
labs/lab_06_capstone_ssot_and_rebuild_test/
├── SPEC.md                                     # This 8-section SSOT contract
├── adversarial_tests/test_rebuild_contract.py  # Read-only verification gate
└── expected_output/taskflow_app.py             # Rebuilt implementation
```

## 7. Environment & Runtime Constraints
- Python 3.11+ standard library only (`typing`). Zero external packages.

## 8. 3-Phase Clean-Room Rebuild Recipe & Acceptance Criteria
- **Phase A (Data & Validation)**: Implement `TaskFlowBoard.__init__` and `add_card` (`REQ-0001`).
- **Phase B (Workflow & Summary)**: Implement `move_card` (`REQ-0002`), `get_by_status` / `get_by_priority` (`REQ-0003`), and `get_summary` (`REQ-0004`).
- **Phase C (Adversarial Verification)**: Run `test_rebuild_contract.py` in a clean room with `adversarial_tests/` locked read-only (`chmod -R a-w`).
