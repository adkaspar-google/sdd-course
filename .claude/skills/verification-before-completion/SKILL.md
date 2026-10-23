---
name: verification-before-completion
description: Enforces the iron law that no task may be marked [x], checkpointed, or archived without fresh, in-turn execution of unit tests, self-diagnosis scripts, and strict spec validation.
---

# Verification Before Completion (`verification-before-completion`)

Combine **Procedural TDD Skill Harness (`verification-before-completion`)** with **Conductor Phase Checkpointing** and **OpenSpec Strict Validation**.

## The Iron Law of Completion

**NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

You may **NEVER**:
- Mark a task `[x]` in `conductor/tracks/<track_id>/plan.md` or `openspec/changes/<change_id>/tasks.md`,
- Create a `conductor(checkpoint)` commit,
- Run `/opsx:archive` (`openspec archive <id>`), or
- Claim to the user that a lab, bugfix, or feature is "complete", "fixed", or "passing"

unless you have executed the verification commands **in the current turn** after the final file edit and confirmed zero failures in the terminal output:

1. **Unit Test Suite**: `CI=true python3 -m unittest` (all `test_reqXXXX_*` tests passing).
2. **Deterministic Lab Gate**: `./self_diagnose.sh` (or `./self_diagnose_all.sh` across all 6 labs).
3. **OpenSpec Schema & Delta Gate** (when OpenSpec CLI is active): `openspec validate --all --strict`.
4. **Workspace Hygiene Check**: `git status --short` confirming no stray temporary files or unapproved edits outside the active track's scope.
