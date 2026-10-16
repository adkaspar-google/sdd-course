# Lab 04 Walkthrough: Spec Drift Detection & 5-Step Brownfield Refactoring (`TaskFlow` Daily Time-Budget Planner)

## 1. Headache-Before-Aspirin & Spiral Retrieval Bridge

### Spiral Retrieval Bridge (From Labs 01–03 $\to$ Lab 04)
In **Lab 02**, we recovered specs from working code (`Sync Spec`), and in **Lab 03**, we implemented code from specs (`Act on Spec`). What happens in Month 3 of a project when **both** `specs/spec.md` and `service/daily_planner.py` exist, a quick hotfix changes a boundary operator in Python, and the spec and code silently diverge? That divergence is **Spec Drift**.

### The Headache (Boundary Drift & "While I'm Here" Scope Creep)
In **Lab 04**, `TaskFlow` includes a **Daily Time-Budget Planner (`DailyPlanner`)** in [`service/daily_planner.py`](./service/daily_planner.py) governed by [`specs/spec.md`](./specs/spec.md). Users set a daily minute budget (such as `120` minutes) and schedule focus tasks into their day.

Look at **`REQ-0003`** in [`specs/spec.md`](./specs/spec.md):
> *`schedule_task(title, minutes)` SHALL return `True` whenever `used_minutes + minutes <= daily_limit_minutes` (including when `remaining_minutes` reaches `0` exactly).*

Now look at line 45 of [`service/daily_planner.py`](./service/daily_planner.py):
```python
if self.used_minutes + minutes >= self.daily_limit_minutes:
    return False
```
Because the developer wrote `>=` instead of `>`, a user with `60` minutes left in their `120`-minute day who tries to schedule a `60`-minute task gets **`False`**! Worse yet, if you ask an unconstrained coding agent to *"Fix `daily_planner.py` and address the scorecard,"* it will also try to implement low-priority wishlist items (`F-02` `.ics` export, `F-03` audio chimes, `F-04` ANSI colors), bloating a 1-line bugfix into a 300-line unreviewable PR.

### The Everyday Metaphor (`Known -> Target`)
Think of the **5-Step Scorecard Refactoring Loop** like an **emergency room triage nurse plus a surgical checklist** (*Known* $\to$ *Target*): you treat the `P0` arterial bleed (`F-01` boundary drift) immediately in the operating room, while explicitly deferring `P3` cosmetic requests (`F-02..F-04`) into `## 6. Out of Scope`.

---

## 2. Step-by-Step Instructions (The 5-Step Scorecard Refactoring Loop)

### Step 1: Audit Spec vs. Code (`Semantic Diffing`)
Compare [`specs/spec.md`](./specs/spec.md) against [`service/daily_planner.py`](./service/daily_planner.py) and review [`scorecard.md`](./scorecard.md):
- **`F-01` (Critical P0)**: Off-by-one `>=` drift bug on line 45 violating `REQ-0003` (`scorecard.md` starts at `0/10` on Boundary Accuracy).
- **`F-02`, `F-03`, `F-04` (Low P3)**: Feature ideas (`.ics` export, audio chimes, ANSI colors).

### Step 2: Scope the Track Spec & Lock `F-02..F-04` in `## 6. Out of Scope`
Write `expected_output/spec.md` targeting only **`F-01`** and placing **`F-02`**, **`F-03`**, and **`F-04`** inside `## 6. Out of Scope` (Karpathy's *Surgical Changes* rule).

### Step 3: Write the Failing Regression Test (`Red`) & Surgical Fix (`Green`)
1. Write `test_req0003_exact_remaining_budget_is_accepted_and_over_budget_rejected` in `test_daily_planner.py` and verify it **fails** against `service/daily_planner.py` (**Red**).
2. Change `>=` to `>` on line 45 in `daily_planner_fixed.py` so the exact boundary (`60 + 60 == 120`) returns `True` (**Green**).

### Step 4: Run Differential Self-Diagnosis (Reference & Custom `work/` Grading)
Note how `self_diagnose.sh` runs a **Differential Regression Gate**: it verifies that `test_req0003` **FAILS** on the buggy `service/daily_planner.py` (`RED` proven!) and **PASSES** on `daily_planner_fixed.py` (`GREEN` proven!):
```bash
# Verify reference solution
./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh

# Grade your own work/ directory
./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh labs/lab_04_drift_detection_and_5step_refactoring/work
```

---

## 3. Common Misconception (`✕` vs. `✓`)

> **✕ Myth:** *"If all tests in `test_daily_planner.py` pass on `daily_planner_fixed.py`, our regression test suite is proved effective."*
>
> **✓ Reality:** A regression test that *also* passes on the unpatched `service/daily_planner.py` (for example, testing `60 + 50 == 110 <= 120` instead of the exact boundary `60 + 60 == 120`) proves nothing! Always verify that your new regression test **fails** against the buggy baseline before applying the fix.

---

## 4. Self-Check Quiz & 3-Rung Hint Ladder

**Question (`Spot-the-Flaw`):** A learner writes a regression test for `F-01` that creates `DailyPlanner(120)`, calls `schedule_task("Deep Work", 60)`, and then calls `schedule_task("Code Review", 55)`, asserting both return `True`. Why will `self_diagnose.sh` reject this test even though `daily_planner_fixed.py` passes all 4 tests?

<details>
<summary><strong>Rung 1 Hint (Spotlight — Where to Look)</strong></summary>
Check how `self_diagnose.sh` tests `test_daily_planner.py` against **both** `expected_output/daily_planner_fixed.py` and the original buggy `service/daily_planner.py`.
</details>

<details>
<summary><strong>Rung 2 Hint (N=1 Toy Case)</strong></summary>
Evaluate the buggy condition `self.used_minutes + minutes >= self.daily_limit_minutes` in `service/daily_planner.py` when `used_minutes = 60` and `minutes = 55`: is `115 >= 120` True or False?
</details>

<details>
<summary><strong>Rung 3 Hint (Full Walkthrough & Answer)</strong></summary>
Because `60 + 55 = 115 < 120`, even the buggy `>=` code in `service/daily_planner.py` returns `True`! The bug only triggers on the exact boundary `used_minutes + minutes == daily_limit_minutes` (`60 + 60 == 120`). Because `self_diagnose.sh` runs your test suite against the unpatched `service/` module first and asserts `test_req0003` **fails** on the buggy code, a weak test (`60 + 55`) passes on the buggy code and fails the differential check!
</details>

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Drift Audit & Scoped Track**:
   - Use **plan mode** for the drift audit with `/opsx:explore` and `/opsx:verify` across `specs/spec.md`, `service/daily_planner.py`, and `scorecard.md`.
   - Run `/conductor:conductor-new-track` with the new track scoped to `F-01` only (`F-02`, `F-03`, and `F-04` in Out of Scope), and save the track specification to `labs/lab_04_drift_detection_and_5step_refactoring/work/spec.md`.
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Clean Implementation Session**: Start a new session (or run `/clear`) before implementing.
5. **Set Goal & Implement**: Set the session goal and run `/conductor:conductor-implement` and `/opsx:apply` to write `test_*.py` and the fixed module under `labs/lab_04_drift_detection_and_5step_refactoring/work/` (leaving `service/daily_planner.py` unmodified):
   ```text
   /goal ./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh work exits 0, shown by running it; no file under adversarial_tests/ or expected_output/ is modified; or stop after 20 turns.
   ```
6. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh work
   ```
