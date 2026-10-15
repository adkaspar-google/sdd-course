# Development Workflow (`conductor/workflow.md`)

## 1. Dual-Engine SDD Protocol
When starting any feature, bugfix, or brownfield refactor via `/conductor:newTrack`:
1. **Skill Activation**: Read and apply `.agents/skills/writing-arch-specs/SKILL.md`.
2. **Contract Alignment**: Ensure `conductor/tracks/<track_id>/spec.md` follows the **7-Section Track Specification Anatomy** (`Overview`, `Architecture & Component Topology`, `Functional Requirements`, `Non-Functional Requirements`, `Acceptance Criteria`, `Out of Scope`, `Verification Commands`) and maps 1:1 to `REQ-XXXX` IDs in `openspec/specs/`.
3. **Hierarchical Plan**: Generate `conductor/tracks/<track_id>/plan.md` broken into small, testable phases ending with `- [ ] Task: Conductor - User Manual Verification '<Phase Name>' (Protocol in workflow.md)`.

## 2. Task TDD Lifecycle (`/conductor:implement`)
For every task in `plan.md`:
1. Mark task `[~]` in `plan.md`.
2. **Red Phase**: Write failing unit test(s) named `test_reqXXXX_<behavior>` in `test_*.py` and run `CI=true python3 -m unittest` to confirm failure.
3. **Green Phase**: Implement the minimal production code required to pass the test and satisfy the RFC 2119 contract.
4. **Refactor Phase**: Clean up types, docstrings, and lock hygiene while keeping tests green.
5. **Commit & Audit Trail**: Commit implementation (`feat:` / `fix:`), attach structured task summary via `git notes add -m "..." <sha>`, and update `plan.md` to `[x] Task: ... <7-char-sha>`.

## 3. Phase Completion Verification & Checkpointing Protocol
At the end of each phase:
1. Verify all changed source files since the previous checkpoint have corresponding `test_reqXXXX_*` tests.
2. Execute `CI=true python3 -m unittest` and `./self_diagnose.sh` (max 2 auto-fix retries on failure).
3. Pause for **User Manual Verification** of the phase outputs.
4. Create checkpoint commit (`conductor(checkpoint): ...`) and record `[checkpoint: <7-char-sha>]` on the phase header in `plan.md`.
5. Synchronize `openspec/specs/` via `/opsx:verify` and `/opsx:archive`.

## 4. Behavioral Guardrails & Immutable Verification (Software 3.0 & Karpathy Rules)
Because code generation is cheap and human verification is the bottleneck, all agent interactions in this repository MUST obey four behavioral rules:
1. **Think Before Coding**: Never make silent assumptions on ambiguous requirements. Pause in Plan Mode (`/conductor:newTrack` or `/opsx:explore`) to surface trade-offs and ask the human before writing code.
2. **Simplicity First**: Write the minimal code required to satisfy the `REQ-XXXX` contract and pass the tests; reject speculative abstractions or unrequested features.
3. **Surgical Changes**: Touch only the files and functions in the active track's scope. Strictly honor `## 6. Out of Scope` and `conductor/tech-stack.md` (halt and ask permission before adding any new dependency).
4. **Goal-Driven Execution & Immutable Verifiers (`autoresearch` Principle)**: Anchor every change to an automated verifier (`test_reqXXXX_*` and `./self_diagnose.sh`). Treat existing test assertions and evaluation harnesses as read-only (`chmod -w` invariant)—never delete or weaken a test to make broken code pass.

## 5. Change Tiering
Not every edit requires full specification ceremony:
1. **Full Track (OpenSpec Change + Conductor Track)**: A full track MUST be used when a change:
   - Adds, modifies, or removes a `REQ-XXXX` requirement;
   - Adds a public function, class, or parameter;
   - Adds a dependency; or
   - Touches more than one non-test source file.
2. **Direct Edit (Lightweight Tier)**: Any other change (such as fixing a typo in a docstring, comment, or local variable name within a single file) MAY be made directly, in which case all tests MUST stay green (`CI=true python3 -m unittest`) and no specification file may change.
3. **Tie-Breaker Rule**: When the tier is unclear, the full track MUST be used.
