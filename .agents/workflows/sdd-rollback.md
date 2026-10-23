---
description: Execute exact specification-level rollback via Inverse Compiler Phi_seq^-1 on conductor/tracks/delta_history.json.
---

Load `.agents/skills/sdd-contract-lock/SKILL.md`:
1. Run `python3 bin/sdd-harness rollback-delta` to invert the latest milestone delta using its logged `BEFORE` preconditions and regenerate a conflict-free `openspec/specs/SPEC.md`.
2. Re-run the test suite to verify post-rollback code parity.
