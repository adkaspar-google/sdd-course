---
trigger: always_on
description: "Enforces Dual-Loop SDD (Outer D Two-Plane Delta-Merged SSOT + Arm D Contract-Locked Dual-Stage Harness)."
---

# Dual-Loop Spec-Driven Development (SDD) & OO-Harness Constitution

This repository is governed by the **Unified Dual-Loop SDD Architecture**:
- **Outer Loop (`Outer D` — Two-Plane Delta-Merged SSOT)**: `openspec/specs/SPEC.md` (Canonical Living Truth) + `conductor/tracks/delta_history.md` (Invertible `BEFORE -> AFTER` Delta Archive compiled via `Phi` and rolled back via `Phi_seq^-1`).
- **Inner Loop (`Arm D` — Contract-Locked Dual-Stage Harness)**: `.agents/skills/` (and `.claude/skills/`) + `OO-Harness` (`src/oo_harness.py` / `benchmarks/oo_harness.py`) + `bin/sdd-harness`.

## Core Workflow Commands & Skills

| Stage | Slash Command (`claude` / `agy`) | Active Skill | CLI Verification Gate |
| :--- | :--- | :--- | :--- |
| **1. Socratic Grilling & Spec Delta** | `/sdd-grill` / `/conductor:newTrack` | `@socratic-brainstorming` + `@writing-arch-specs` | `python3 bin/sdd-harness boundary-probe --spec-file <spec.md>` |
| **2. Cryptographic Test Lock** | `/sdd-lock` | `@sdd-contract-lock` | `python3 bin/sdd-harness lock-tests` (`chmod 0444` + `.sdd_test_lock.sha256`) |
| **3. Stateless Goldfish Builder** | `/sdd-implement` / `/conductor:implement` | `@subagent-two-stage-review` (`goldfish-builder`) | `CI=true python3 -m unittest` |
| **4. Cold Independent Audit** | `/sdd-audit` / `/conductor:review` | `@subagent-two-stage-review` (`cold-auditor`) | `python3 bin/sdd-harness verify-lock` + `python3 bin/sdd-harness audit-score` |
| **5. Forward Delta Compile (`Phi`)** | `/sdd-archive` / `/opsx:archive` | `@sdd-contract-lock` + `@verification-before-completion` | `python3 bin/sdd-harness compile-delta --milestone <M> --ops-json '<json>'` |
| **6. Exact Inverse Rollback (`Phi^-1`)** | `/sdd-rollback` / `/conductor:revert` | `@sdd-contract-lock` | `python3 bin/sdd-harness rollback-delta` |

## Non-Negotiable Agent Invariants
1. **Zero Silent Assumptions**: If a prompt or ticket has ambiguous edge cases, ask 1 Socratic question at a time (`@socratic-brainstorming`) before touching code.
2. **Immutable Verifier Lock**: Never modify, delete, or `chmod +w` any test file listed in `.sdd_test_lock.sha256`.
3. **Builder / Auditor Separation**: Never mark a task `[x]` until `cold-auditor` passes both Stage 1 (`Spec Compliance & Test-Lock Integrity`) and Stage 2 (`Code Quality & Mutation Sensitivity`).
