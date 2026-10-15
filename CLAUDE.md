# SDD-Crash-Course — Claude Code Project Rules

## Commands & Environment
- Language: Python 3.11+ standard library only (zero external runtime packages).
- Test runner: `CI=true python3 -m unittest` (or `CI=true python3 -m unittest discover -s <dir> -p "test_*.py" -v`).
- Lab grader: `./labs/<lab>/self_diagnose.sh [TARGET_DIR]` (defaults to `expected_output`; pass `work` in learner mode).
- Full suite: `CI=true ./self_diagnose_all.sh`.

## Core Invariants
- Requirement traceability: every requirement `REQ-XXXX` MUST be verified by a unit test named `test_reqXXXX_*`.
- Immutable verifiers: `adversarial_tests/` is strictly read-only (`chmod -w` and `Edit(**/adversarial_tests/**)` denied). Never modify or weaken existing test assertions to make broken code pass.
- In learner mode (`claude --settings .claude/learner.settings.json`), `expected_output/` is hidden via `Read(**/expected_output/**)` deny rules; write your deliverables under `labs/<lab>/work/`.

## Workflow & Change Tiering
- Follow `conductor/workflow.md` for the Dual-Engine SDD protocol, Red-Green-Refactor TDD lifecycle, phase checkpointing, and the **Change Tiering** rule (`## 5. Change Tiering` in `conductor/workflow.md`).
- Conductor commands use `/conductor:<skill>` (`conductor-setup`, `conductor-new-track`, `conductor-implement`, `conductor-review`, `conductor-revert`, `conductor-status`).
- OpenSpec commands use `/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:verify`, and `/opsx:archive`.
- Architecture specification formatting rules live in `.agents/skills/writing-arch-specs/SKILL.md` and `openspec/config.yaml`.
