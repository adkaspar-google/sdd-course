---
name: sdd-contract-lock
description: Executes the 4-Step Contract-Locked Dual-Stage Harness (Arm D) and Two-Plane Delta-Merged SSOT Forward/Inverse Compiler (Outer D: Phi and Phi_seq^-1) using bin/sdd-harness, goldfish-builder, cold-auditor, and repair-agent.
---

# Contract-Locked Dual-Stage Harness & Delta Compiler (`@sdd-contract-lock`)

This skill bridges the interactive **Conductor + OpenSpec** course workflow with the automated **4-Step Contract-Locked Dual-Stage Harness (`Arm D`)** and **Two-Plane Delta-Merged SSOT Compiler (`Outer D`)** validated across the 252-trial benchmark.

## 1. Inner-Loop 4-Step Contract-Locked Protocol (`Arm D`)

1. **Step 1 — Cryptographic Test Lock (`chmod 0444` + SHA-256 Manifest)**:
   ```bash
   python3 bin/sdd-harness lock-tests
   ```
   Writes `.sdd_test_lock.sha256` (recording SHA-256 digests and AST `test_*` function names) and sets `chmod 0444` on all baseline/contract test files.
2. **Step 2 — Automated Boundary Probing (`c-1, c, c+1`)**:
   ```bash
   python3 bin/sdd-harness boundary-probe --spec-file openspec/specs/SPEC.md
   ```
   Extracts integer and floating-point boundary literals from the active specification and generates `(c - 1, c, c + 1)` triples.
3. **Step 3 — Stateless Goldfish Builder Dispatch**:
   Delegate implementation to the `goldfish-builder` subagent. The `PreToolUse` hook (`scripts/verify_test_lock_hook.py`) physically blocks any attempt to edit or `chmod +w` locked test files.
4. **Step 4 — Cold Independent Auditor + AST Prefix Check (`P_AST`)**:
   ```bash
   python3 bin/sdd-harness verify-lock
   ```
   Dispatch the read-only `cold-auditor` subagent. If `cold-auditor` returns `REJECT`, dispatch `repair-agent` (bounded by a 3-round circuit breaker).

## 2. Outer-Loop Forward & Inverse Delta Compiler (`Outer D`: `Phi` & `Phi_seq^-1`)

- **Forward Delta Compilation (`Phi(S_{t-1}, Delta_t)`)**:
  ```bash
  python3 bin/sdd-harness compile-delta --milestone M1 --ops-json '[{"op":"ADDED","id":"REQ-0001","after":"System SHALL..."}]'
  ```
  Compiles structured `ADDED`, `MODIFIED`, `REMOVED`, and `RENAMED` delta tuples into `openspec/specs/SPEC.md` and appends invertible `BEFORE -> AFTER` records to `conductor/tracks/delta_history.md`.
- **Exact Specification-Level Rollback (`Phi_seq^-1`)**:
  ```bash
  python3 bin/sdd-harness rollback-delta
  ```
  Inverts the most recent milestone delta in reverse order (`M4 -> M3/M2`) with `0.0%` active clause contradictions.
