# Development Workflow (`conductor/workflow.md`)

> **Architecture:** **Outer-Loop Specification & State Governance (`Conductor` + `OpenSpec` + `SPEC.md`)** $\times$ **Inner-Loop Agent Behavioral Discipline (`Claude Superpowers` / `.agents/skills/`)**

## 1. Outer-Loop + Inner-Loop SDD Protocol (`/conductor:newTrack` & `/opsx:propose`)
When starting any feature, bugfix, or brownfield refactor via `/conductor:newTrack` or `/opsx:propose`:
1. **Socratic Brainstorming (`@socratic-brainstorming`)**: Apply the Single-Question Policy ("The Grill"), propose 2–3 architectural trade-off options (`ADR-XXXX`), validate design blocks incrementally (200–300 words), and apply YAGNI (`## 6. Out of Scope`). Never write orphan date-stamped `docs/superpowers/specs/YYYY-MM-DD-*.md` files—route all specs directly into `openspec/changes/<id>/` and `conductor/tracks/<track_id>/`.
2. **Contract Alignment (`@writing-arch-specs`)**: Ensure `conductor/tracks/<track_id>/spec.md` follows the **7-Section Track Specification Anatomy** (`Overview`, `Architecture`, `Functional Requirements`, `Non-Functional Requirements`, `Acceptance Criteria`, `Out of Scope`, `Verification Commands`) and maps 1:1 to `REQ-XXXX` IDs and 4-hashtag `#### Scenario:` blocks in `openspec/specs/`.
3. **Bite-Sized Hierarchical Plan**: Generate `conductor/tracks/<track_id>/plan.md` (and `openspec/changes/<id>/tasks.md`) broken into atomic 2–5 minute TDD tasks (`Audit -> RED -> GREEN -> REFACTOR & Verify`) ending each phase with `- [ ] Task: Conductor - User Manual Verification '<Phase Name>' (Protocol in workflow.md)`.

## 2. Inner-Loop Task TDD & Subagent Lifecycle (`/conductor:implement` & `/opsx:apply`)
For every task in `plan.md` / `tasks.md` (governed by `@subagent-two-stage-review`):
1. Mark task `[~]` in `plan.md` and dispatch a fresh, stateless ("Goldfish") Implementer context (isolated in a git worktree when running parallel tracks).
2. **Audit**: Inspect local module dependencies, test fixtures, and `conductor/tech-stack.md` before writing code.
3. **Red Phase (TDD Iron Law)**: Write failing unit test(s) named `test_reqXXXX_<behavior>` in `test_*.py` and run `CI=true python3 -m unittest` to confirm failure. Delete any production code written before a failing test.
4. **Green Phase**: Implement the minimal production code required to pass the test and satisfy the RFC 2119 contract.
5. **4-Phase Systematic Debugging Gate (`@systematic-debugging-gate`)**: If any test or command fails twice in a row, HALT blind edits and execute the 4-phase root-cause protocol (Spec-to-Code Semantic Diff $\to$ Fixture Trace $\to$ Minimal Reproduction Test $\to$ Surgical Fix).
6. **Mandatory Two-Stage Review (`@subagent-two-stage-review`)**:
   - **Stage 1 (`Spec Compliance Review`)**: Confirm 100% `REQ-XXXX` & `#### Scenario:` satisfaction and `## 6. Out of Scope` compliance.
   - **Stage 2 (`Code Quality & Constitution Review`)**: Only after Stage 1 is `✅`, audit adherence to `conductor/tech-stack.md`, `conductor/code_styleguides/`, and regression safety.
7. **Verification Before Completion (`@verification-before-completion`) & Commit**: Execute fresh `CI=true python3 -m unittest` and `./self_diagnose.sh` in the current turn, commit implementation (`feat:` / `fix:`), attach structured task summary via `git notes add -m "..." <sha>`, and update `plan.md` to `[x] Task: ... <7-char-sha>`.

## 3. Phase Completion Verification & Checkpointing Protocol
At the end of each phase:
1. Verify all changed source files since the previous checkpoint have corresponding `test_reqXXXX_*` tests.
2. Execute fresh `CI=true python3 -m unittest` and `./self_diagnose.sh` (`@verification-before-completion` iron law).
3. Pause for **User Manual Verification** of the phase outputs.
4. Create checkpoint commit (`conductor(checkpoint): ...`) and record `[checkpoint: <7-char-sha>]` on the phase header in `plan.md`.
5. Synchronize `openspec/specs/` via `/opsx:verify` and `/opsx:archive`.

## 4. Behavioral Guardrails & Immutable Verification (Software 3.0 & Karpathy Rules)
Because code generation is cheap and human verification is the bottleneck, all agent interactions in this repository MUST obey four behavioral rules:
1. **Think Before Coding**: Never make silent assumptions on ambiguous requirements. Pause in Plan Mode (`/conductor:newTrack` or `/opsx:explore`) to surface trade-offs and ask the human before writing code.
2. **Simplicity First**: Write the minimal code required to satisfy the `REQ-XXXX` contract and pass the tests; reject speculative abstractions or unrequested features.
3. **Surgical Changes**: Touch only the files and functions in the active track's scope. Strictly honor `## 6. Out of Scope` and `conductor/tech-stack.md` (halt and ask permission before adding any new dependency).
4. **Goal-Driven Execution & Immutable Verifiers (`autoresearch` Principle)**: Anchor every change to an automated verifier (`test_reqXXXX_*` and `./self_diagnose.sh`). Treat existing test assertions and evaluation harnesses as read-only (`chmod -w` invariant)—never delete or weaken a test to make broken code pass.

## 5. Risk-Proportional Change Tiering (Avoiding Ceremony Bloat)
To keep developer velocity high without sacrificing specification integrity, match workflow ceremony to change risk:
- **Tier 1 — Trivial Fix** (typos, doc comments, 1-line formatting with zero behavioral change): Direct edit + `@verification-before-completion` test run.
- **Tier 2 — Single-Module Bugfix or Scoped Enhancement** (touches 1 capability, `< 50` lines): Lightweight OpenSpec delta (`/opsx:propose`) + 4-phase `@systematic-debugging-gate` + TDD test (`test_reqXXXX_*`) + `/opsx:archive`.
- **Tier 3 — Cross-Cutting Feature, New Capability, or Architectural Change**: Full Outer-Loop (`Conductor` Track + `OpenSpec` Delta + `ADR-XXXX`) + Inner-Loop (`@socratic-brainstorming`, `@subagent-two-stage-review`, `$N+1$ Stacked PRs`, or `SPEC.md` Clean-Room Rebuild Test).
