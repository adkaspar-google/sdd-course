# Technology Stack

## Languages & Runtime
- **Language**: Python 3.11+ (strictly typed with standard library `typing` and `dataclasses`).
- **Concurrency Primitives**: `threading.RLock` for thread-safe in-memory state transitions.

## Testing & Verification
- **Test Runner**: `python3 -m unittest` (compatible with `pytest`).
- **Coverage Target**: `>80%` line and branch coverage; 100% requirement coverage (`REQ-XXXX` -> `test_reqXXXX_*`).
- **Diagnostic Harness**: Bash `./self_diagnose.sh` per lab and `./self_diagnose_all.sh` at repository root.

## Specification & Context Tooling
- **Context & TDD Track Engine**: Conductor (`/conductor:setup`, `/conductor:newTrack`, `/conductor:implement`, `/conductor:review`, `/conductor:revert`).
- **Capability Contract & Delta Engine**: OpenSpec (`@fission-ai/openspec` — `/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:verify`, `/opsx:archive`).
- **System-Level SSOT Blueprint**: Canonical 8-Section `SPEC.md` verified via the Clean-Room Rebuild Test.
- **Dedicated Specification Skill**: `.agents/skills/writing-arch-specs/SKILL.md`.
