# Lab 03 Walkthrough: From Specs to TDD Code — Act on Spec (`TaskFlow` Daily Habit Streak Tracker)

## 1. Headache-Before-Aspirin & Spiral Retrieval Bridge

### Spiral Retrieval Bridge (From Labs 01–02 $\to$ Lab 03)
In **Lab 01** and **Lab 02**, we authored and recovered normative capability specifications (`REQ-0001..REQ-0004` with `#### Scenario:` blocks). Now in **Lab 03**, we close the forward loop with **Act on Spec (`Apply`)**: turning an approved specification into verified production code via strict **Red $\to$ Green $\to$ Refactor** Test-Driven Development.

### The Headache (Code-First Implementation Without Traceable Tests)
In **Lab 03**, you are given an approved specification in [`specs/spec.md`](./specs/spec.md) and [`specs/design.md`](./specs/design.md) for `TaskFlow`'s **Daily Habit Streak Tracker (`habit_tracker.py`)**—just like a Duolingo daily streak counter using simple integer day numbers (`Day 1`, `Day 2`, `Day 3...`). When an AI agent writes `habit_tracker.py` first and writes tests *afterward*, it suffers from **Sycophantic Self-Testing**: if the agent forgets that a same-day duplicate check-in (`day == last_day`) should be a no-op, it simply writes unit tests that never test duplicate check-ins—reporting `100% PASS` on broken logic!

### The Everyday Metaphor (`Known -> Target`)
Think of **Requirement-Traceable TDD (`test_req0001..0004` before `habit_tracker.py`)** like **installing the target goalposts and scoreboard sensor before kicking a soccer ball** (*Known* $\to$ *Target*). If the player gets to paint the goalposts *after* kicking the ball, every kick magically counts as a goal.

---

## 2. Step-by-Step Instructions

### Step 1: Review the Approved 4-Requirement Contract
Read [`specs/spec.md`](./specs/spec.md) and verify how the 4 requirements partition the integer day number line relative to `last_check_in_day`:
- **`REQ-0001` (`add_habit`)**: Trims `name`, initializes `streak = 0` and `last_check_in_day = None`, and raises `ValueError` if empty.
- **`REQ-0002` (`check_in` Consecutive Day)**: Sets `streak = 1` on first check-in (`last_check_in_day is None`) and increments `streak += 1` when `day == last_check_in_day + 1`.
- **`REQ-0003` (`check_in` Same-Day Idempotence)**: Checking in again on the same day (`day == last_check_in_day`) leaves `streak` unchanged.
- **`REQ-0004` (`check_in` Gap Reset & Back-Dating Rejection)**: Skipping one or more days (`day > last_check_in_day + 1`) resets `streak = 1`; checking in on a past day (`day < last_check_in_day`) or `day < 1` raises `ValueError`.

### Step 2: Execute TDD Implementation with Subagent Two-Stage Review (`/conductor:implement` + `@subagent-two-stage-review`)
Apply the **Outer-Loop (`Conductor` + `OpenSpec`) + Inner-Loop (`@subagent-two-stage-review`)** protocol ([`../../.agents/skills/subagent-two-stage-review/SKILL.md`](../../.agents/skills/subagent-two-stage-review/SKILL.md)):
1. **Bite-Sized Task Plan (`tasks.md`)**: Break `REQ-0001..REQ-0004` into ordered 2–5 minute tasks (`Audit -> RED -> GREEN -> REFACTOR & Verify`) with zero topological inversions.
2. **Red Phase (TDD Iron Law)**: Write the 4 failing unit tests in `test_habit_tracker.py` (`test_req0001_*` through `test_req0004_*`, each with a docstring `Verifies REQ-000X: ...`) and confirm they fail (**Red**). Delete any implementation code written before a failing test.
3. **Green & Refactor Phase**: Implement `HabitTracker` in `habit_tracker.py` to make all 4 tests pass (**Green**), then clean up (**Refactor**).
4. **Mandatory Two-Stage Cold Auditor Gate**:
   - **Stage 1 (`Spec Compliance & Anti-Reward-Hacking`)**: Confirm 1:1 `REQ-0001..0004` coverage and real behavioral assertions (no smoke tests).
   - **Stage 2 (`Code Quality & Constitution`)**: Confirm `conductor/tech-stack.md` compliance and run `@verification-before-completion`.

- **Conductor / OpenSpec Command**:
  ```text
  /conductor:implement Implement HabitTracker in habit_tracker.py and test_habit_tracker.py from specs/spec.md using @subagent-two-stage-review and Red-Green-Refactor TDD with test_req0001..0004 naming.
  ```

### Step 3: Verify Your Deliverables (Reference & Custom `work/` Grading)
```bash
# Verify reference solution
./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh

# Grade your own work/ directory
./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh labs/lab_03_from_specs_to_tdd_code/work
```

---

## 3. Common Misconception (`✕` vs. `✓`)

> **✕ Myth:** *"Naming unit tests `test_habit_tracker_works()` is fine as long as line coverage is over 80%."*
>
> **✓ Reality:** Generic test names hide requirement gaps. Naming every test `test_reqXXXX_<behavior>` with a `Verifies REQ-XXXX` docstring creates a deterministic 1-to-1 audit link between `specs/spec.md` and `test_habit_tracker.py` that CI scripts (`self_diagnose.sh`) can verify in `< 50ms`.

---

## 4. Self-Check Quiz & 3-Rung Hint Ladder

**Question (`Predict-the-Outcome`):** A user creates `"Morning Run"` (`streak = 0`) and calls:
1. `check_in("Morning Run", day=1)`
2. `check_in("Morning Run", day=2)`
3. `check_in("Morning Run", day=2)`
4. `check_in("Morning Run", day=5)`
5. `check_in("Morning Run", day=6)`

What is the returned `streak` after each of the 5 calls, and what happens if they next call `check_in("Morning Run", day=4)`?

<details>
<summary><strong>Rung 1 Hint (Spotlight — Where to Look)</strong></summary>
Trace `gap = day - last_day` across `REQ-0002` (`gap == 1`), `REQ-0003` (`gap == 0`), and `REQ-0004` (`gap > 1` vs. `gap < 0`).
</details>

<details>
<summary><strong>Rung 2 Hint (N=1 Toy Case)</strong></summary>
After `day=2`, `streak` is `2` and `last_day` is `2`. Calling `day=2` again has `gap = 0` (`REQ-0003` idempotent no-op $\to$ `2`). Calling `day=5` has `gap = 5 - 2 = 3 > 1` (`REQ-0004` gap reset $\to$ `1`).
</details>

<details>
<summary><strong>Rung 3 Hint (Full Walkthrough & Answer)</strong></summary>
The 5 calls return **`1, 2, 2, 1, 2`**:
- `day=1`: first check-in $\to$ **`1`** (`last_day=1`)
- `day=2`: `gap == 1` (`REQ-0002`) $\to$ **`2`** (`last_day=2`)
- `day=2`: `gap == 0` (`REQ-0003`) $\to$ **`2`** (`last_day=2`)
- `day=5`: `gap == 3 > 1` (`REQ-0004` reset) $\to$ **`1`** (`last_day=5`)
- `day=6`: `gap == 1` (`REQ-0002`) $\to$ **`2`** (`last_day=6`)
Calling `check_in("Morning Run", day=4)` next has `day < last_day` (`4 < 6`), which violates **`REQ-0004`** and raises **`ValueError`** without mutating `streak` or `last_day`.
</details>
