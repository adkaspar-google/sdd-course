# Lab 02 Walkthrough: Brownfield Spec Recovery & Spec Sync (`TaskFlow` Tag & Priority Organizer)

## 1. Scenario & Spec-Driven Testing / Sync Spec
In **Lab 02**, a teammate added [`service/task_organizer.py`](./service/task_organizer.py) and [`service/test_task_organizer.py`](./service/test_task_organizer.py) to `TaskFlow` so users can tag tasks (`["Work", "urgent"]`) and sort them by priority (`high` $\to$ `medium` $\to$ `low`). All 4 unit tests pass, but **no specification or ADR exists**.

In Spec-Driven Development, this is the **Sync Spec** operation: we inspect existing code and tests in read-only exploration mode and extract the living capability contract (`openspec/specs/task-organizer/spec.md`) and architecture decision record (`ADR-0001-tag-normalization.md`) *without modifying the working service code*.

---

## 2. Step-by-Step Instructions

### Step 1: Explore the Brownfield Code & Tests Without Editing Code
- **OpenSpec Command**:
  ```text
  /opsx:explore Read labs/lab_02_brownfield_spec_recovery/service/task_organizer.py and test_task_organizer.py and list the 4 behavioral requirements (REQ-0001..REQ-0004).
  ```

### Step 2: Recover the OpenSpec Capability Contract (`REQ-0001..REQ-0004`)
Document the 4 contracts in `openspec/specs/task-organizer/spec.md`:
1. **`REQ-0001` (Tag Normalization)**: Trim, lowercase, and deduplicate tags; reject empty titles or empty tags with `ValueError`.
2. **`REQ-0002` (Priority Validation)**: Only allow `"low"`, `"medium"`, or `"high"` (default `"medium"`).
3. **`REQ-0003` (Case-Insensitive Tag Filter)**: `filter_by_tag(tag)` matches case-insensitively in creation order.
4. **`REQ-0004` (Priority Sorting)**: `list_by_priority()` sorts `"high"` $\to$ `"medium"` $\to$ `"low"` with creation order (`id`) breaking ties.

### Step 3: Record `ADR-0001-tag-normalization.md`
Document why tags are normalized to lowercase on write inside `add_task()`.

### Step 4: Verify Your Deliverables
```bash
./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh
```
