---
name: systematic-debugging-gate
description: Enforces a 4-phase root-cause debugging protocol whenever a test or verification command fails twice in a row, prohibiting blind trial-and-error code patching.
---

# 4-Phase Systematic Debugging Gate (`systematic-debugging-gate`)

Combine **Claude Superpowers (`systematic-debugging`)** with **OpenSpec Semantic Diffing** and **Conductor Drift Remediation**.

## Trigger Condition

Invoke this skill immediately whenever:
- A unit test (`test_reqXXXX_*`) or `./self_diagnose.sh` fails **twice in a row**, OR
- You are diagnosing a brownfield **Spec-to-Code Drift** defect (such as Lab 04's `daily_planner.py` budget boundary bug).

## Iron Law: Zero Blind Guessing

**NEVER** randomly tweak operators, add defensive `try/except: pass` blocks, or edit test assertions to make a red test green. You MUST complete Phases 1–3 before modifying production code in Phase 4:

1. **Phase 1 — Spec-to-Code Semantic Diff**:
   - Place the normative `REQ-XXXX` statement and `#### Scenario:` block side-by-side with the exact lines of production code.
   - Check relational operators (`>` vs. `>=`, `<` vs. `<=`), ordering direction (`list()` vs. `reversed()`), and state mutation boundaries (`gap == 1` vs. `gap > 1`).
2. **Phase 2 — Fixture & Input Trace**:
   - Trace the exact concrete input values from the failing scenario through the function step-by-step (e.g., `used=420`, `minutes=60`, `max_minutes=480` $\implies$ `420 + 60 = 480`).
3. **Phase 3 — Minimal Failing Reproduction Test**:
   - Verify that a dedicated unit test (`test_reqXXXX_*`) isolates the exact boundary condition and fails deterministically before touching production code.
4. **Phase 4 — Surgical Single-Point Fix**:
   - Apply the minimal change required to align the code with `REQ-XXXX`, while keeping all `Out of Scope` scorecard items untouched.
