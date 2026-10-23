# Lab 01 Walkthrough: Greenfield Proposals to Dual-Engine Specs (`TaskFlow` Core To-Do List)

## 1. Headache-Before-Aspirin: Why Conversational Coding Fails Here
Welcome to **Lab 01** of the **`TaskFlow`** journey! You have a short product note in [`proposal.md`](./proposal.md) asking for a **To-Do List (`todo_list.py`)** where users can add tasks, mark them complete, filter pending vs. completed tasks, and delete tasks.

### The Headache (Conversational Coding / "Vibe Coding")
When a developer pastes [`proposal.md`](./proposal.md) directly into an LLM chat and says *"Write the code,"* the LLM optimizes for token plausibility and silently guesses every missing boundary condition:
- Does `add_task("   ")` create a blank task or raise `ValueError`?
- Are task IDs random UUID strings (`"a8f9..."`) or sequential integers (`1, 2, 3...`)?
- Does `complete_task(999)` return `False` while `delete_task(999)` crashes with `KeyError`—or the reverse?

### The Everyday Metaphor (`Known -> Target`)
Think of [`proposal.md`](./proposal.md) as a **back-of-napkin sketch for a kitchen renovation** (*Known*), and the **OpenSpec + Conductor Spec Contract** as the **stamped architectural blueprint with exact electrical and plumbing measurements** (*Target*). You never let a contractor start knocking down walls from a napkin sketch before locking down where the pipes and outlets go.

---

## 2. Step-by-Step Instructions

### Step 1: Run Interactive Socratic Grilling ("The Grill" + `@socratic-brainstorming`)
Inspect [`proposal.md`](./proposal.md) using OpenSpec exploration paired with our Inner-Loop Socratic Brainstorming skill ([`../../.agents/skills/socratic-brainstorming/SKILL.md`](../../.agents/skills/socratic-brainstorming/SKILL.md)):
- **Inner-Loop Procedural TDD Skill Harness Discipline (`brainstorming`)**: Ask clarifying questions **one at a time**, propose 2–3 architectural alternatives with explicit trade-offs (`ADR-0001` & `ADR-0002`), validate in concise 200–300 word blocks, and apply ruthless YAGNI (`## 6. Out of Scope`).
- **Outer-Loop Destination Rule**: Unlike standalone Procedural TDD Skill (which writes date-stamped `docs/procedural_tdd_skill/specs/YYYY-MM-DD-*-design.md` files that rot over time), route all validated specs directly into the living `openspec/specs/todo-list/spec.md` and `conductor/tracks/` tree.

- **OpenSpec Command**:
  ```text
  /opsx:explore Read labs/lab_01_greenfield_proposals_to_specs/proposal.md using @socratic-brainstorming and list the 3 ambiguity questions we must lock down before writing the spec.
  ```
- **Socratic Grilling Answers to Lock In**:
  1. **Blank Titles (`REQ-0001`)**: Strip leading/trailing whitespace and raise `ValueError` if the resulting title is empty.
  2. **Task IDs (`ADR-0002`)**: Assign deterministic sequential integers (`1, 2, 3...`) starting at `1`, never reusing deleted IDs.
  3. **Missing IDs (`REQ-0002` vs. `REQ-0004`)**: `complete_task(task_id)` raises `KeyError` (strict state transition on a known task), whereas `delete_task(task_id)` returns `False` (idempotent cleanup).

### Step 2: Generate the OpenSpec Capability Contract & ADRs
- **OpenSpec Command**:
  ```text
  /opsx:propose Create the todo-list capability spec (REQ-0001..REQ-0004) with 4-hashtag Scenarios and RFC 2119 SHALL/MUST keywords, plus ADR-0001-storage-engine.md and ADR-0002-id-assignment.md.
  ```

### Step 3: Generate the 7-Section Conductor Track Spec & Plan
- **Conductor Command**:
  ```text
  /conductor:newTrack Create track todo_list_mvp using .agents/skills/writing-arch-specs/SKILL.md with all 7 required sections (including Section 6: Out of Scope).
  ```

### Step 4: Verify Your Deliverables (Reference & Custom `work/` Grading)
Compare your generated files against [`expected_output/`](./expected_output/) and run the self-diagnosis script (or pass your own `work` folder to grade your custom deliverables):
```bash
# Verify reference solution
./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh

# Grade your own work/ directory
./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh labs/lab_01_greenfield_proposals_to_specs/work
```

---

## 3. Common Misconception (`✕` vs. `✓`)

> **✕ Myth:** *"Socratic Grilling slows down greenfield velocity—it is faster to let the LLM generate `todo_list.py` first and fix edge cases in chat later."*
>
> **✓ Reality:** Fixing a wrong ID-assignment or error-handling assumption *after* code and tests are generated requires multi-turn chat debugging that pollutes the context window. Answering 3 Socratic questions upfront takes 30 seconds and locks `REQ-0001..REQ-0004` into a deterministic contract before a single line of Python is written.

---

## 4. Self-Check Quiz & 3-Rung Hint Ladder

**Question (`Spot-the-Flaw`):** A learner writes the following OpenSpec scenario block inside `openspec/specs/todo-list/spec.md`:
```markdown
### Requirement: REQ-0001 Add Task with Trimmed Title
The `TodoList` SHALL trim whitespace and reject empty task titles.

### Scenario: Blank title is rejected
- **WHEN** `add_task("   ")` is called
- **THEN** `ValueError` is raised
```
Why will `openspec validate --strict` fail on this requirement even though the `WHEN`/`THEN` text looks reasonable?

<details>
<summary><strong>Rung 1 Hint (Spotlight — Where to Look)</strong></summary>
Look closely at the Markdown heading level (`#` count) on the `Scenario:` line compared to the `Requirement:` line.
</details>

<details>
<summary><strong>Rung 2 Hint (N=1 Toy Case)</strong></summary>
OpenSpec's AST parser expects `### Requirement:` at heading level 3 (`3` hashtags) and every child scenario nested underneath it at heading level 4 (`4` hashtags: `#### Scenario:`). What happens when `### Scenario:` uses only `3` hashtags?
</details>

<details>
<summary><strong>Rung 3 Hint (Full Walkthrough & Answer)</strong></summary>
Because `### Scenario:` uses 3 hashtags instead of 4 (`#### Scenario:`), the OpenSpec Markdown AST parser closes the `REQ-0001` block early, treats `Scenario:` as a malformed sibling heading, and reports **`0` scenarios** under `REQ-0001`—triggering a strict validation error (`Every Requirement MUST contain at least one #### Scenario:`). Changing `### Scenario:` to `#### Scenario:` fixes the AST hierarchy immediately.
</details>
