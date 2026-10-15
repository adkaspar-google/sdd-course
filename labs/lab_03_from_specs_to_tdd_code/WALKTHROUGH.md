# Lab 03 Walkthrough: From Specs to TDD Code — Act on Spec (`TaskFlow` Daily Habit Streak Tracker)

## 1. Scenario & "Act on Spec" (`Apply`)
In **Lab 03**, you are given an approved specification in [`specs/spec.md`](./specs/spec.md) and [`specs/design.md`](./specs/design.md) for `TaskFlow`'s **Daily Habit Streak Tracker (`habit_tracker.py`)**—just like a Duolingo daily streak counter using simple integer day numbers (`Day 1`, `Day 2`, `Day 3...`).

In Specificational Coding, once the human and agent agree on the spec, the agent executes **Act on Spec (`Apply`)**:
1. Break the 4 requirements (`REQ-0001..REQ-0004`) into ordered tasks in `tasks.md`.
2. For each requirement, write a failing unit test named `test_req000X_*` (**Red**), write the minimal Python code in `habit_tracker.py` to pass it (**Green**), and clean up (**Refactor**).

---

## 2. Step-by-Step Instructions

### Step 1: Review the Approved 4-Requirement Contract
Read [`specs/spec.md`](./specs/spec.md):
- **`REQ-0001`**: `add_habit(name)` trims `name`, starts `streak = 0`, and raises `ValueError` if empty.
- **`REQ-0002`**: `check_in(name, day)` sets `streak = 1` on first check-in and increments `streak += 1` when `day == last_day + 1`.
- **`REQ-0003`**: Checking in again on the same day (`day == last_day`) leaves `streak` unchanged.
- **`REQ-0004`**: Skipping a day (`day > last_day + 1`) resets `streak = 1`; checking in on a past day (`day < last_day`) raises `ValueError`.

### Step 2: Execute TDD Implementation (`/conductor:implement` / `/opsx:apply`)
- **Conductor / OpenSpec Command**:
  ```text
  /conductor:implement Implement HabitTracker in habit_tracker.py and test_habit_tracker.py from specs/spec.md using Red-Green-Refactor TDD with test_req0001..0004 naming.
  ```

### Step 3: Verify Your Deliverables
```bash
./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh
```


---

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Plan the Track**: Inspect `labs/lab_03_from_specs_to_tdd_code/specs/spec.md` and `specs/design.md` in **plan mode**, then run `/conductor:conductor-new-track` and `/opsx:propose` to prepare the phased TDD plan.
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Clean Implementation Session**: Start a new session (or run `/clear`) before implementing so implementation begins with clean context.
5. **Set Goal & Implement**: Set the session goal and run `/conductor:conductor-implement` and `/opsx:apply` to write `test_habit_tracker.py` and `habit_tracker.py` in `labs/lab_03_from_specs_to_tdd_code/work/`:
   ```text
   /goal ./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh work exits 0, shown by running it; no file under adversarial_tests/ or expected_output/ is modified; or stop after 20 turns.
   ```
6. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh work
   ```
