---
description: Dispatch the stateless Goldfish Builder to implement the approved REQ-XXXX task under read-only test lock protection.
---

Load `.agents/skills/subagent-two-stage-review/SKILL.md` and `.agents/skills/sdd-contract-lock/SKILL.md`:
1. Ensure tests are locked (`python3 bin/sdd-harness lock-tests` if `.sdd_test_lock.sha256` does not yet exist).
2. Dispatch the `goldfish-builder` subagent on the target task (`$ARGUMENTS`), enforcing `Audit -> RED -> GREEN -> Refactor` and boundary probing `(c-1, c, c+1)`.
3. After implementation, run `python3 bin/sdd-harness verify-lock` and `CI=true python3 -m unittest`.
