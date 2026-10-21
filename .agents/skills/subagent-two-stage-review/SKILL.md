---
name: subagent-two-stage-review
description: Dispatches fresh stateless ("Goldfish") Implementer subagents per task with read-only adversarial test locks, 4-state builder reporting, and a Cold Independent Auditor executing a Two-Stage Review (Stage 1 Spec Compliance & Anti-Reward-Hacking -> Stage 2 Code Quality & Constitution).
---

# Subagent Execution & Two-Stage Review (`subagent-two-stage-review`)

Combine **Claude Superpowers (`subagent-driven-development`)**, the **Elephant-Goldfish Model (EGM)**, **Closed-Loop Builder/Auditor Separation**, and **Conductor + OpenSpec**.

## 1. Elephant vs. Goldfish Separation (Pre-Code Spec Stress-Test)

- **The Elephant (Co-Design Session)**: Accumulates conversational context with the human while shaping `spec.md` and `plan.md`. Because the Elephant mentally fills in unwritten assumptions, it must **never** trust its own memory as proof that a spec is unambiguous.
- **Pre-Code Goldfish DAG Check**: Before dispatching implementation tasks, verify `plan.md` / `tasks.md` with fresh eyes for **Zero Topological Inversions** (ensuring no task `Task k` imports a class, exception, or helper function that isn't defined until `Task k+1`) and compute the **Objective Defect-Anchored Readiness Score**:
  $$\text{Score} = \max(0.0,\; 10.0 - 3.0 \times P_0 - 1.0 \times P_1 - 0.2 \times P_2)$$
  where $P_0$ = blocking spec gap or topological inversion, $P_1$ = unmapped `REQ-XXXX` or missing error policy, and $P_2$ = minor formatting drift. Proceed to implementation when $P_0 = 0$ and $P_1 = 0$.

## 2. Stateless ("Goldfish") Builder Dispatch & 4-State Status Protocol

For each discrete task (`- [ ] Task: ...`) in `conductor/tracks/<track_id>/plan.md` or `openspec/changes/<change_id>/tasks.md`:
1. **Session Isolation**: Dispatch a fresh **Implementer (Builder)** subagent with only:
   - The active task description and target file paths ($\le 150$ lines per slice)
   - The governing `REQ-XXXX` contract from `spec.md`
   - `conductor/tech-stack.md` and `conductor/workflow.md`
2. **Adversarial Test Lock (`chmod -w` Invariant)**: When contract or adversarial tests are pre-scaffolded (as in Capstone Rebuild tests), the Builder subagent has **zero permission** to modify, delete, or weaken test assertions.
3. **4-Step Implementer Task Lifecycle**:
   - **Step 1 — Audit**: Check local module imports, existing test fixtures, and `tech-stack.md` constraints.
   - **Step 2 — RED**: Write or run the failing `test_reqXXXX_<behavior>` test and verify it fails for the expected reason.
   - **Step 3 — GREEN**: Write the minimal production code in `service/` or `src/` to pass the test.
   - **Step 4 — REFACTOR & Verify**: Clean up types/docstrings and run `CI=true python3 -m unittest` and `./self_diagnose.sh`.
4. **4-State Builder Status Report (Anti-Reward-Hacking Escape Hatch)**:
   - Every Builder subagent must conclude with an explicit status token:
     - `STATUS: DONE` — Task implemented and verified.
     - `STATUS: DONE_WITH_CONCERNS` — Passes tests, but surfaces a boundary edge case for review.
     - `STATUS: NEEDS_CONTEXT` — **Halts immediately** if `spec.md` contradicts real codebase APIs instead of guessing or reward-hacking tests.
     - `STATUS: BLOCKED` — External environment or dependency blocker.

## 3. Mandatory Two-Stage Cold Auditor Gate (With 3-Round Circuit Breaker)

Never mark a task `[x]` until a **Cold Independent Auditor** (fresh context with zero sunk-cost bias) passes **both** sequential review stages (bounded by a maximum **3-round circuit breaker** before escalating to the human):

1. **Stage 1 — Spec Compliance & Anti-Reward-Hacking Review (`spec-reviewer`)**:
   - **Zero-Trust Diff Audit**: Inspects the raw `git diff` directly rather than trusting the Builder's summary prose.
   - **Requirement & Scenario Parity**: Does the code satisfy every normative `MUST` / `SHALL` statement and every `#### Scenario:` (`GIVEN / WHEN / THEN`) in `REQ-XXXX`?
   - **Anti-Smoke-Test & Mutation Sensitivity**: Do `test_reqXXXX_*` tests contain real behavioral assertions that would fail if the production logic were mutated (banning vacuous `assert res is not None` smoke tests)?
   - **Negative Scope Lock**: Did the Builder respect `## 6. Out of Scope` (zero unrequested features or gold-plating)?
2. **Stage 2 — Code Quality & Constitution Review (`code-quality-reviewer`)**:
   - *Strict Gating*: Never start Stage 2 until Stage 1 is `✅ PASS`.
   - Does the code obey `conductor/tech-stack.md` (zero unapproved dependencies) and `conductor/code_styleguides/`?
   - Did any cumulative `REQ-XXXX` behavior across the module regress (e.g., mutated sort order or off-by-one boundary drift)?
