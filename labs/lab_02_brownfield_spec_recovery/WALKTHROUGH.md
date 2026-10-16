# Lab 02 Walkthrough: Brownfield Spec Recovery & Spec Sync (`TaskFlow` Tag & Priority Organizer)

## 1. Headache-Before-Aspirin & Spiral Retrieval Bridge

### Spiral Retrieval Bridge (From Lab 01 $\to$ Lab 02)
In **Lab 01**, we practiced **Greenfield Forward Specification** (`proposal.md` $\to$ Socratic Grill $\to$ `REQ-0001..REQ-0004` + ADRs). In real engineering teams, however, you rarely start from an empty repository—you inherit **brownfield code** where features already work in production, but no specification exists.

### The Headache (Modifying Un-Specced Brownfield Code)
In **Lab 02**, a teammate added [`service/task_organizer.py`](./service/task_organizer.py) and [`service/test_task_organizer.py`](./service/test_task_organizer.py) to `TaskFlow` so users can tag tasks (`["Work", "urgent"]`) and sort them by priority (`high` $\to$ `medium` $\to$ `low`). All 4 unit tests pass, but **no specification or ADR exists**. If an AI agent is asked to add a new feature directly to `task_organizer.py` without recovering its baseline spec first, it can easily break subtle invariants (such as stable tie-breaking by task `id` or lowercase tag deduplication on write).

### The Everyday Metaphor (`Known -> Target`)
Think of **Brownfield Spec Recovery (`Sync Spec`)** like **laser-scanning an historic building to generate as-built CAD blueprints before adding a new wing** (*Known* $\to$ *Target*). During the scan, your laser scanner is strictly read-only—you never swing a sledgehammer while measuring the existing walls.

---

## 2. Step-by-Step Instructions

### Step 1: Explore the Brownfield Code & Tests in Read-Only Mode
Use OpenSpec's exploration mode (`/opsx:explore`) to trace the exact behavior of [`service/task_organizer.py`](./service/task_organizer.py) and [`service/test_task_organizer.py`](./service/test_task_organizer.py) without modifying a single line of Python:

- **OpenSpec Command**:
  ```text
  /opsx:explore Read labs/lab_02_brownfield_spec_recovery/service/task_organizer.py and test_task_organizer.py and list the 4 behavioral requirements (REQ-0001..REQ-0004) with exact file:line citations.
  ```

### Step 2: Recover the OpenSpec Capability Contract (`REQ-0001..REQ-0004`)
Document the 4 as-built behavioral contracts in `openspec/specs/task-organizer/spec.md`:
1. **`REQ-0001` (Tag Normalization)**: Strip whitespace, lowercase, and deduplicate tags preserving first-seen order (`[" Work ", "urgent", "work"]` $\to$ `["work", "urgent"]`); reject empty titles or empty tags with `ValueError`.
2. **`REQ-0002` (Priority Validation)**: Only allow `"low"`, `"medium"`, or `"high"` (default `"medium"`); reject invalid priorities with `ValueError`.
3. **`REQ-0003` (Case-Insensitive Tag Filter)**: `filter_by_tag(tag)` normalizes the query (`tag.strip().lower()`) and returns matching tasks in creation order (`id`).
4. **`REQ-0004` (Priority Sorting)**: `list_by_priority()` sorts `"high"` (`0`) $\to$ `"medium"` (`1`) $\to$ `"low"` (`2`) with creation order (`id`) breaking ties deterministically.

### Step 3: Record `ADR-0001-tag-normalization.md`
Document the architectural decision explaining why tags are normalized to lowercase **on write** inside `add_task()` rather than normalizing every tag repeatedly on read inside `filter_by_tag()`.

### Step 4: Verify Your Deliverables (Reference & Custom `work/` Grading)
```bash
# Verify reference solution (and confirm service/task_organizer.py was not modified)
./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh

# Grade your own work/ directory
./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh labs/lab_02_brownfield_spec_recovery/work
```

---

## 3. Common Misconception (`✕` vs. `✓`)

> **✕ Myth:** *"While recovering a brownfield spec (`Sync Spec`), if the agent notices a cleaner way to write `task_organizer.py`, it should refactor the Python code at the same time."*
>
> **✓ Reality:** Mixing **Spec Recovery (`Sync`)** with **Code Refactoring (`Apply`)** destroys your baseline truth. If a test breaks, you cannot tell whether the spec was wrong or the refactor broke behavior. Always lock `Sync Spec` as a 100% read-only operation against `service/` first.

---

## 4. Self-Check Quiz & 3-Rung Hint Ladder

**Question (`Predict-the-Outcome`):** Suppose `TaskOrganizer` has two `"high"` priority tasks (`id=1` `"Submit tax form"` and `id=3` `"Pay rent"`) and one `"medium"` priority task (`id=2` `"Buy coffee"`). In what exact order does `list_by_priority()` return the task IDs, and which expression in `service/task_organizer.py` guarantees this?

<details>
<summary><strong>Rung 1 Hint (Spotlight — Where to Look)</strong></summary>
Inspect the `key=` lambda passed to `sorted(...)` inside `list_by_priority()` in [`service/task_organizer.py`](./service/task_organizer.py).
</details>

<details>
<summary><strong>Rung 2 Hint (N=1 Toy Case)</strong></summary>
Look at the tuple returned by the sort key for each task: `(PRIORITY_RANK[t["priority"]], t["id"])`. Compute that 2-tuple for `id=1` (`"high"`), `id=2` (`"medium"`), and `id=3` (`"high"`).
</details>

<details>
<summary><strong>Rung 3 Hint (Full Walkthrough & Answer)</strong></summary>
Since `PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}`, the sort keys are:
- `id=1`: `(0, 1)`
- `id=3`: `(0, 3)`
- `id=2`: `(1, 2)`
Sorting those tuples ascending yields **`[1, 3, 2]`**. That second tuple element (`t["id"]`) is the exact invariant documented in **`REQ-0004`** (*creation order breaks ties among equal-priority tasks*).
</details>

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, start Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Audit & Recover Spec**:
   - Use **plan mode** for the audit with `/opsx:explore`, and use **subagents** for tracing `service/task_organizer.py` and `service/test_task_organizer.py` without modifying source files.
   - Run `/opsx:propose` to author the recovered OpenSpec contract and ADR, collecting your deliverables under `labs/lab_02_brownfield_spec_recovery/work/` (`openspec/specs/task-organizer/spec.md` and `ADR-0001-tag-normalization.md`).
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh work
   ```
