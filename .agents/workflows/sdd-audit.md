---
description: Run the read-only Cold Independent Auditor (Stage 1 Spec & Test-Lock Compliance -> Stage 2 Code Quality & Mutation Sensitivity).
---

Load `.agents/skills/subagent-two-stage-review/SKILL.md`:
1. Run `python3 bin/sdd-harness verify-lock` to verify zero test tampering.
2. Dispatch the read-only `cold-auditor` subagent to inspect `git diff` against `openspec/specs/SPEC.md` and `conductor/tech-stack.md`.
3. Compute the readiness score via `python3 bin/sdd-harness audit-score --p0 <P0> --p1 <P1> --p2 <P2>`. If rejected, invoke `repair-agent` (max 3 rounds).
