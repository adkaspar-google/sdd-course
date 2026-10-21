# Lab 05 Walkthrough: SDD Code Review, Spec Sync & Stacked PRs (`TaskFlow` Quick Notes Board)

## 1. Headache-Before-Aspirin & Spiral Retrieval Bridge

### Spiral Retrieval Bridge (From Labs 01–04 $\to$ Lab 05)
In **Lab 04**, we caught a 1-character spec drift (`>=` vs. `>`) that slipped into the codebase. How do we prevent spec drift and un-specced features from ever merging into `main` in the first place? In **Lab 05**, we move upstream to **SDD Code Review (`/conductor:review` + `/opsx:verify`) and Stacked Pull Requests**.

### The Headache (Reviewing Code Diffs Without Checking the Spec Contract)
In **Lab 05**, `TaskFlow` has a working **Quick Notes Board** in [`base/notes_board.py`](./base/notes_board.py) backed by [`base/openspec/specs/notes-board/spec.md`](./base/openspec/specs/notes-board/spec.md) (`REQ-0001..REQ-0003`). A teammate submits [`simulated_review/subpar_change.patch`](./simulated_review/subpar_change.patch) to add **"Pinned Notes"**. In a traditional code-only review, a reviewer glances at the Python diff, sees clean syntax, and clicks `LGTM`. Yet when you run an **SDD Code Review**, you immediately catch **3 serious architectural violations**:
1. **Silent Contract Break (`REQ-0002`)**: `REQ-0002` requires `list_notes()` to return notes in chronological creation order (`1, 2, 3...`), but the patch wrapped `list_notes()` in `reversed(...)`!
2. **Un-Specced Feature (`REQ-0004` Missing)**: The patch added `pin_note(note_id)` and `get_pinned_notes()` in Python without adding `REQ-0004` to `openspec/specs/notes-board/spec.md`.
3. **Silent Missing-ID Bug**: `pin_note(note_id)` silently ignores unknown IDs (`return False`) instead of raising `KeyError` like the rest of `TaskFlow`.

### The Everyday Metaphor (`Known -> Target`)
Think of **SDD Code Review & Stacked PRs (`Batch 1 -> Batch 2 -> Archive PR N+1`)** like **customs inspection at a port of entry** (*Known* $\to$ *Target*): every shipping container (`PR`) must match its bill of lading (`spec.md`), and you inspect one container at a time rather than dumping 10 containers into a single pile.

---

## 2. Step-by-Step Instructions

### Step 1: Two-Stage Cold Auditor Review on `subpar_change.patch` (`/conductor:review` + `@subagent-two-stage-review`)
Run `/conductor:review` and `/opsx:verify` using the **Two-Stage Cold Auditor Protocol** ([`../../.agents/skills/subagent-two-stage-review/SKILL.md`](../../.agents/skills/subagent-two-stage-review/SKILL.md)) on [`simulated_review/subpar_change.patch`](./simulated_review/subpar_change.patch) against [`base/openspec/specs/notes-board/spec.md`](./base/openspec/specs/notes-board/spec.md):
- **Stage 1 (`Spec Compliance & Regression Audit`)**: Catches the `reversed()` break on `REQ-0002` and the un-specced `pin_note` method (`REQ-0004` missing).
- **Stage 2 (`Code Quality & Error Contract Audit`)**: Catches `pin_note(note_id)` returning `False` instead of raising `KeyError` on unknown IDs.
```text
/conductor:review Audit labs/lab_05_sdd_code_review_and_stacked_prs/simulated_review/subpar_change.patch against base/openspec/specs/notes-board/spec.md using @subagent-two-stage-review and report all contract violations.
```

### Step 2: Synchronize the Spec (`REQ-0004`) & Fix `notes_board.py`
1. Add **`REQ-0004` (`Pin Note and List Pinned Notes`)** with 4-hashtag `#### Scenario:` blocks to `openspec/specs/notes-board/spec.md`.
2. Restore chronological order in `list_notes()` (`REQ-0002`) and raise `KeyError` on unknown `note_id` in `pin_note(note_id)` (`REQ-0004`).
3. Split `tasks.md` into **Batch 1 (Spec Delta & Contract Tests)**, **Batch 2 (Implementation & Review Fixes)**, and **Archive PR N+1 (`openspec archive`)** for Stacked PR review.

### Step 3: Verify Your Deliverables (Reference & Custom `work/` Grading)
```bash
# Verify reference solution
./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh

# Grade your own work/ directory
./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh labs/lab_05_sdd_code_review_and_stacked_prs/work
```

---

## 3. Common Misconception (`✕` vs. `✓`)

> **✕ Myth:** *"In a stacked 3-PR feature (`PR 1`, `PR 2`, `PR 3`), you should run `openspec archive` inside `PR 1` so the main spec is updated right away."*
>
> **✓ Reality:** Running `openspec archive` inside `PR 1` deletes the active change folder `openspec/changes/<id>/` while `PR 2` and `PR 3` are still in flight, causing merge conflicts and premature spec promotion. Always keep the change folder active across `PR 1..N` and execute `openspec archive` in a dedicated **`Archive PR N+1`** after all implementation batches have merged.

---

## 4. Self-Check Quiz & 3-Rung Hint Ladder

**Question (`Spot-the-Flaw`):** In [`simulated_review/subpar_change.patch`](./simulated_review/subpar_change.patch), why is changing `return list(self._notes)` to `return list(reversed(self._notes))` inside `list_notes()` a **`CRITICAL` SDD violation** even if the author claims *"Newest notes first looks nicer in the UI"*?

<details>
<summary><strong>Rung 1 Hint (Spotlight — Where to Look)</strong></summary>
Read **`REQ-0002` (`Chronological Note Listing`)** in [`base/openspec/specs/notes-board/spec.md`](./base/openspec/specs/notes-board/spec.md).
</details>

<details>
<summary><strong>Rung 2 Hint (N=1 Toy Case)</strong></summary>
Suppose note `1` (`"First"`) and note `2` (`"Second"`) are added. `REQ-0002` explicitly states `WHEN list_notes() is called THEN notes are returned in chronological order [1, 2]`. What does `list(reversed(self._notes))` return?
</details>

<details>
<summary><strong>Rung 3 Hint (Full Walkthrough & Answer)</strong></summary>
`list(reversed(self._notes))` returns `[2, 1]`, directly breaking the normative **`REQ-0002`** contract that downstream callers depend on. In Spec-Driven Development, an implementation patch is **never** allowed to silently contradict an active `REQ-XXXX` contract: either the code must obey `REQ-0002` (`[1, 2]`), or the author must first propose and gain approval for a `## MODIFIED Requirements` spec delta updating `REQ-0002`.
</details>

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Spec Compliance & Bug Review**:
   - Run `/conductor:conductor-review` and `/opsx:verify` for spec compliance, then `/code-review` for bugs, with the instruction to report only requirement or correctness gaps.
   - Run `/opsx:propose` and `/conductor:conductor-new-track` to synchronize `REQ-0004` in `labs/lab_05_sdd_code_review_and_stacked_prs/work/openspec/specs/notes-board/spec.md` and decompose the work into Stacked PR batches in `labs/lab_05_sdd_code_review_and_stacked_prs/work/tasks.md`.
3. **Human Approval Checkpoint**: Read the spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Clean Implementation Session**: Start a new session (or run `/clear`) before implementing.
5. **Set Goal & Implement**: Set the session goal and run `/conductor:conductor-implement` and `/opsx:apply` to write `notes_board.py` and `test_notes_board.py` under `labs/lab_05_sdd_code_review_and_stacked_prs/work/`:
   ```text
   /goal ./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh work exits 0, shown by running it; no file under adversarial_tests/ or expected_output/ is modified; or stop after 20 turns.
   ```
6. **Verify**: Run the self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh work
   ```
