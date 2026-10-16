# Lab 06 Walkthrough: Capstone — 8-Section `SPEC.md` (SSOT) & Clean-Room Rebuild Test (`TaskFlowBoard`)

## 1. Headache-Before-Aspirin & Spiral Retrieval Bridge

### Spiral Retrieval Bridge (From Labs 01–05 $\to$ Lab 06 Capstone)
Across **Labs 01–05**, we built and governed individual capabilities of **`TaskFlow`** (`TodoList`, `TaskOrganizer`, `HabitTracker`, `DailyPlanner`, `NotesBoard`) using OpenSpec delta contracts and Conductor TDD tracks. In **Lab 06 (Capstone)**, we reach **Level 3 SDD Maturity (Spec-as-Source / Single Source of Truth)**: synthesizing a complete system from an 8-Section [`SPEC.md`](./SPEC.md) alone and proving it via the **Clean-Room Rebuild Test**.

### The Headache (Specifications That Decay into Stale Wiki Pages)
Most engineering design docs rot within weeks of launch because source code is treated as the only real truth. If you deleted `src/` today and handed your team's design doc to a clean-room AI agent, could it regenerate a working implementation that passes an independent adversarial test suite on the first run? If not, your specification is missing **Essential Domain Intent** (or is polluted with coupled implementation trivia).

### The Everyday Metaphor (`Known -> Target`)
Think of **Level 3 Spec-as-SSOT & The Clean-Room Rebuild Test** like **compiling C++ source code into an executable binary (`gcc main.cpp -o app`)** (*Known* $\to$ *Target*): [`SPEC.md`](./SPEC.md) is the human-owned source code, [`taskflow_app.py`](./expected_output/taskflow_app.py) is the compiled binary artifact, and [`adversarial_tests/test_rebuild_contract.py`](./adversarial_tests/test_rebuild_contract.py) (locked read-only!) is the hardware verification bench.

---

## 2. Step-by-Step Instructions

### Step 1: Audit the 8-Section `SPEC.md` Contract (`REQ-0001..REQ-0004`)
Read [`SPEC.md`](./SPEC.md) and verify all 8 canonical sections (especially **Section 3: Data Models**, **Section 4: Interface Contracts**, and **Section 8: Rebuild Recipe & Acceptance Criteria**):
1. **`REQ-0001` (`add_card`)**: Trim `title` (reject empty with `ValueError`), validate `priority in {"low", "medium", "high"}` and `points > 0` (`ValueError` otherwise), and initialize `status = "todo"` with sequential integer `id` (`1, 2, 3...`).
2. **`REQ-0002` (`move_card` & WIP Limit)**: Move cards across `"todo"`, `"in_progress"`, and `"done"` (`KeyError` on unknown `card_id`, `ValueError` on invalid `new_status`), while raising **`RuntimeError`** if moving a card into `"in_progress"` would exceed `max_in_progress` (note: moving a card that is *already* `"in_progress"` to `"in_progress"` is a no-op and must not fail!).
3. **`REQ-0003` (`get_by_status` & `get_by_priority`)**: Return matching cards in creation order (`id`), raising `ValueError` on invalid status/priority filters.
4. **`REQ-0004` (`get_summary`)**: Return `{"total": int, "todo": int, "in_progress": int, "done": int, "completed_points": int}` where `completed_points` sums `points` strictly for cards in `"done"`.

### Step 2: Synthesize `taskflow_app.py` in a Clean Room from `SPEC.md` Alone
Generate `taskflow_app.py` using [`SPEC.md`](./SPEC.md) as the sole architectural input. Notice that [`adversarial_tests/test_rebuild_contract.py`](./adversarial_tests/test_rebuild_contract.py) is locked read-only (`chmod -w`) so the implementer agent cannot weaken the test assertions!

### Step 3: Run the Clean-Room Rebuild Test (Reference & Custom `work/` Grading)
```bash
# Verify reference clean-room rebuild against read-only adversarial_tests/
./labs/lab_06_capstone_ssot_and_rebuild_test/self_diagnose.sh

# Grade your own clean-room rebuild in work/taskflow_app.py
./labs/lab_06_capstone_ssot_and_rebuild_test/self_diagnose.sh labs/lab_06_capstone_ssot_and_rebuild_test/work
```

---

## 3. Common Misconception (`✕` vs. `✓`)

> **✕ Myth:** *"To make `SPEC.md` rebuildable, we should paste private helper function names, local loop variable names, and internal dict keys into `SPEC.md`."*
>
> **✓ Reality:** Pasting private implementation details into `SPEC.md` violates the **Essential vs. Incidental Complexity Boundary**—turning your spec into brittle pseudocode. `SPEC.md` must lock **100% of observable behavioral entropy** ($H(B(C)\mid S) \approx 0$: public class/method signatures, input validation, state transitions, WIP limits, and return schemas) while leaving private internal helper structures unconstrained.

---

## 4. Self-Check Quiz & 3-Rung Hint Ladder

**Question (`Predict-the-Outcome`):** A `TaskFlowBoard(max_in_progress=2)` currently has two cards in `"in_progress"` (`card_id=1` with `3` points and `card_id=2` with `5` points) and one card in `"todo"` (`card_id=3` with `8` points).
1. What happens when `move_card(3, "in_progress")` is called?
2. What happens when `move_card(1, "in_progress")` is called (moving card `1` which is *already* in `"in_progress"` to `"in_progress"`)?
3. If `move_card(1, "done")` is called next, what does `get_summary()["completed_points"]` return?

<details>
<summary><strong>Rung 1 Hint (Spotlight — Where to Look)</strong></summary>
Inspect **`REQ-0002`** (`move_card` WIP limit check) and **`REQ-0004`** (`get_summary` `completed_points` calculation) in [`SPEC.md`](./SPEC.md).
</details>

<details>
<summary><strong>Rung 2 Hint (N=1 Toy Case)</strong></summary>
When `card_id=3` (`status="todo"`) moves to `"in_progress"`, the number of `"in_progress"` cards would become `3 > max_in_progress (2)`. What about when `card_id=1` (`status="in_progress"`) is moved to `"in_progress"` (`card["status"] != "in_progress"` is `False`)?
</details>

<details>
<summary><strong>Rung 3 Hint (Full Walkthrough & Answer)</strong></summary>
1. `move_card(3, "in_progress")` raises **`RuntimeError`** because `2` cards (`id=1, 2`) are already `"in_progress"` and adding a third would exceed `max_in_progress=2` (`REQ-0002`).
2. `move_card(1, "in_progress")` **succeeds without raising `RuntimeError`** because card `1` is *already* in `"in_progress"`, so the count of `"in_progress"` cards remains `2`.
3. After `move_card(1, "done")`, card `1` (`3` points) is the only card in `"done"`, so `get_summary()["completed_points"]` returns **`3`** (`REQ-0004`).
</details>
