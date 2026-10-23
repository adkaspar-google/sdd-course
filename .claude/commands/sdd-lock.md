---
description: Lock baseline and contract tests with SHA-256 digests (.sdd_test_lock.sha256) and read-only chmod 0444 permissions before Builder execution.
---

Load `.agents/skills/sdd-contract-lock/SKILL.md` and execute Step 1 of the Contract-Locked Dual-Stage Harness (`Arm D`):
1. Run `python3 bin/sdd-harness lock-tests` to record SHA-256 hashes and AST `test_*` function names in `.sdd_test_lock.sha256` and apply `chmod 0444`.
2. Confirm that `python3 bin/sdd-harness verify-lock` exits with code `0`.
