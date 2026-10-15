# Lab 05 Walkthrough: SDD Code Review, Spec Sync & Stacked PRs (`TaskFlow` Quick Notes Board)

## 1. Scenario & The 3 SDD Violations in `subpar_change.patch`
In **Lab 05**, `TaskFlow` has a working **Quick Notes Board** in [`base/notes_board.py`](./base/notes_board.py) backed by [`base/openspec/specs/notes-board/spec.md`](./base/openspec/specs/notes-board/spec.md) (`REQ-0001..REQ-0003`).

A teammate submits [`simulated_review/subpar_change.patch`](./simulated_review/subpar_change.patch) to add **"Pinned Notes"**, but when you run SDD Code Review (`/conductor:review` and `/opsx:verify`), you catch **3 violations**:
1. **Contract Break (`REQ-0002`)**: `REQ-0002` requires `list_notes()` to return notes in chronological creation order (`1, 2, 3...`), but the patch wrapped `list_notes()` in `reversed(...)`!
2. **Un-Specced Feature (`REQ-0004` Missing)**: The patch added `pin_note(note_id)` and `get_pinned_notes()` in Python without updating `openspec/specs/notes-board/spec.md`.
3. **Silent Missing-ID Bug**: `pin_note(note_id)` silently ignores unknown IDs instead of raising `KeyError`.

---

## 2. Step-by-Step Instructions

### Step 1: Audit `subpar_change.patch` Against the Spec
Run `/conductor:review` and `/opsx:verify` on [`simulated_review/subpar_change.patch`](./simulated_review/subpar_change.patch).

### Step 2: Synchronize the Spec (`REQ-0004`) & Fix `notes_board.py`
1. Add **`REQ-0004` (`Pin Note and List Pinned Notes`)** to `openspec/specs/notes-board/spec.md`.
2. Restore chronological order in `list_notes()` (`REQ-0002`) and raise `KeyError` on unknown `note_id` in `pin_note(note_id)` (`REQ-0004`).
3. Split `tasks.md` into **Batch 1**, **Batch 2**, and **Archive PR N+1** for Stacked PR review.

### Step 3: Verify Your Deliverables
```bash
./labs/lab_05_sdd_code_review_and_stacked_prs/self_diagnose.sh
```


---

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
