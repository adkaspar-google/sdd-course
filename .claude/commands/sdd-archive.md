---
description: Compile verified capability deltas into openspec/specs/SPEC.md via Forward Compiler Phi and log invertible BEFORE -> AFTER tuples in conductor/tracks/delta_history.md.
---

Load `.agents/skills/sdd-contract-lock/SKILL.md` and `.agents/skills/verification-before-completion/SKILL.md`:
1. Verify fresh test execution (`CI=true python3 -m unittest`) and lock integrity (`python3 bin/sdd-harness verify-lock`).
2. Run `python3 bin/sdd-harness compile-delta --milestone <MILESTONE_ID> --ops-json '<DELTA_OPS_JSON>'` to merge the delta into `openspec/specs/SPEC.md` and append to `conductor/tracks/delta_history.md`.
