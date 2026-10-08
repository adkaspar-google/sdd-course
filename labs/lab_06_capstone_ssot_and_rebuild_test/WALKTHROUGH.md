# Lab 06 (Capstone): The 8-Section `SPEC.md` (SSOT) & Clean-Room Rebuild Test

**Estimated Time**: 60 minutes  
**Frameworks Practiced**: Canonical 8-Section `SPEC.md` (Spec-as-SSOT) + Adversarial Clean-Room Rebuild Test

---

## 1. Learning Objective
At **SDD Maturity Level 3 (Spec-as-Source / SSOT)**, your specification is complete enough that you can delete the implementation, copy `SPEC.md` into an empty `/tmp/` directory, and deterministically regenerate a working implementation that passes an independently authored, read-only adversarial test suite on the first run.

In this capstone lab, you will inspect the **8-Section `SPEC.md`** for the **CoursePulse University Enrollment & Waitlist Service** and run the **Clean-Room Rebuild Verification Protocol**:
1. Lock `adversarial_tests/test_rebuild_contract.py` read-only (`chmod -R a-w`) inside an isolated clean-room directory so the implementation under test cannot weaken or delete assertions.
2. Verify that `expected_output/coursepulse.py` satisfies every contract in `SPEC.md` (`REQ-0001` through `REQ-0006`).

---

## 2. Starting Input
- [`SPEC.md`](./SPEC.md): Complete 8-Section Single Source of Truth blueprint (`1. System Overview & Domain Intent`, `2. Architecture & Data Flow`, `3. Data Models & Schemas`, `4. Interface & API Contracts`, `5. Behavioral Workflows & State Machines`, `6. Repository Structure`, `7. Parameterized Deployment & Runtime Config`, `8. 3-Phase Rebuild Recipe & Acceptance Criteria`).
- [`adversarial_tests/test_rebuild_contract.py`](./adversarial_tests/test_rebuild_contract.py): Read-only adversarial contract test suite verifying `REQ-0001` through `REQ-0006`.

---

## 3. Self-Diagnosis & Clean-Room Rebuild Execution
Run `./self_diagnose.sh` to execute the Clean-Room Rebuild Test in an isolated temporary directory with read-only adversarial tests:

```bash
./self_diagnose.sh
```
