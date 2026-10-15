# Lab 01 Walkthrough: Greenfield Proposals to Dual-Engine Specs (`TaskFlow` Core To-Do List)

## 1. Scenario & Why Conversational Coding Fails Here
Welcome to **Lab 01** of the **`TaskFlow`** journey! You have a short product note in [`proposal.md`](./proposal.md) asking for a **To-Do List (`todo_list.py`)** where users can add tasks, mark them complete, filter pending vs. completed tasks, and delete tasks.

In **conversational coding ("Vibe Coding")**, a developer pastes `proposal.md` directly into an LLM chat and says *"Write the code."* The LLM silently guesses edge cases:
- Does `add_task("   ")` create a blank task or raise `ValueError`?
- Are task IDs random UUID strings or integers `1, 2, 3...`?
- Does `delete_task(999)` crash with `KeyError` or return `False`?

In **Specificational Coding (Spec-Driven Development)**, we collaborate with the agent on the **Spec Contract** *before* writing code.

---

## 2. Step-by-Step Instructions

### Step 1: Run Interactive Socratic Grilling ("The Grill")
Inspect [`proposal.md`](./proposal.md) using OpenSpec exploration so the agent identifies missing edge cases before generating any spec or code:

- **OpenSpec Command**:
  ```text
  /opsx:explore Read labs/lab_01_greenfield_proposals_to_specs/proposal.md and list the 3 ambiguity questions we must lock down before writing the spec.
  ```
- **Socratic Grilling Answers to Lock In**:
  1. **Blank Titles (`REQ-0001`)**: Trim whitespace and raise `ValueError` if empty.
  2. **Task IDs (`ADR-0002`)**: Use sequential integers (`1, 2, 3...`) starting at `1`.
  3. **Missing IDs (`REQ-0002` vs. `REQ-0004`)**: `complete_task(id)` raises `KeyError`, while `delete_task(id)` returns `False`.

### Step 2: Generate the OpenSpec Capability Contract & ADRs
- **OpenSpec Command**:
  ```text
  /opsx:propose Create the todo-list capability spec (REQ-0001..REQ-0004) with 4-hashtag Scenarios and RFC 2119 SHALL/MUST keywords, plus ADR-0001-storage-engine.md and ADR-0002-id-assignment.md.
  ```

### Step 3: Generate the 7-Section Conductor Track Spec & Plan
- **Conductor Command**:
  ```text
  /conductor:newTrack Create track todo_list_mvp using .agents/skills/writing-arch-specs/SKILL.md with all 7 required sections.
  ```

### Step 4: Verify Your Deliverables
Compare your generated files against [`expected_output/`](./expected_output/) and run the self-diagnosis script:
```bash
./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh
```


---

## Claude Code Track

1. **Start in Learner Mode**: From the repository root on a personal branch, launch Claude Code with learner settings so `expected_output/` is hidden and `adversarial_tests/` is locked:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Explore & Specify**:
   - Enter **plan mode** to read `labs/lab_01_greenfield_proposals_to_specs/proposal.md` without writing files.
   - Run `/opsx:propose` and `/conductor:conductor-new-track` to produce the OpenSpec capability contract, ADRs, and 7-section Conductor track specification, collecting your deliverables under `labs/lab_01_greenfield_proposals_to_specs/work/` (`openspec/specs/todo-list/spec.md`, `conductor/tracks/todo_list_mvp/spec.md`, `ADR-0001-storage-engine.md`, `ADR-0002-id-assignment.md`; `test_*.py` is optional).
3. **Human Approval Checkpoint**: Read the generated spec and plan, run `git status --short`, and confirm only specification artifacts changed.
4. **Verify**: Run the targetable self-diagnosis script against your `work/` directory:
   ```bash
   ./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh work
   ```
