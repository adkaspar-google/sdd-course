# Lab 06 Walkthrough: Capstone — 8-Section `SPEC.md` (SSOT) & Clean-Room Rebuild Test (`TaskFlowBoard`)

## 1. Scenario & Code as a Compiled Artifact of the Spec
Welcome to the **Lab 06 Capstone**! The ultimate goal of Specificational Coding is to make **source code a compiled artifact of the specification**—just as machine code is a compiled artifact of source code.

In this lab, you are given [`SPEC.md`](./SPEC.md): the complete 8-section Single Source of Truth contract for **`TaskFlowBoard` (`taskflow_app.py`)**, a Kanban board that tracks cards across `"todo"`, `"in_progress"`, and `"done"`, enforces a `max_in_progress` Work-In-Progress limit, and computes a summary scorecard with completed story points.

---

## 2. Step-by-Step Instructions

### Step 1: Read the 8-Section `SPEC.md` Contract (`REQ-0001..REQ-0004`)
1. **`REQ-0001` (`add_card`)**: Trim `title`, validate `priority in {"low", "medium", "high"}` and `points > 0`, and start in `"todo"`.
2. **`REQ-0002` (`move_card`)**: Move cards across `"todo"`, `"in_progress"`, and `"done"` while raising `RuntimeError` if moving a card into `"in_progress"` would exceed `max_in_progress`.
3. **`REQ-0003` (`get_by_status` & `get_by_priority`)**: Filter cards in creation order.
4. **`REQ-0004` (`get_summary`)**: Return `total`, `todo`, `in_progress`, `done`, and `completed_points`.

### Step 2: Synthesize `taskflow_app.py` from `SPEC.md` Alone
Generate `taskflow_app.py` using [`SPEC.md`](./SPEC.md) as the only input, without editing [`adversarial_tests/test_rebuild_contract.py`](./adversarial_tests/test_rebuild_contract.py).

### Step 3: Run the Clean-Room Rebuild Test
```bash
./labs/lab_06_capstone_ssot_and_rebuild_test/self_diagnose.sh
```
