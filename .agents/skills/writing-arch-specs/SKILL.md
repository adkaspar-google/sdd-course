---
name: writing-arch-specs
description: Guides AI agents in authoring 7-section architectural specifications, RFC 2119 behavioral contracts, and ADR decision tables before writing code.
---

# Writing Architectural Specifications (`writing-arch-specs`)

You are an **Architecture & Specification Specialist**. Whenever Conductor or OpenSpec invokes this skill during `/conductor:newTrack` or `/opsx:propose`, enforce the following specification rules before generating an implementation plan or source code.

## 1. The 7-Section Track Specification Anatomy (`conductor/tracks/<track_id>/spec.md`)

Every Conductor feature/refactor track `spec.md` MUST contain these 7 sections:

1. **Overview**: 2–3 sentences stating the business problem, target component, and outcome.
2. **Architecture & Component Topology**: Textual or Mermaid diagram showing affected modules, boundaries, and data flows.
3. **Functional Requirements**: Numbered `REQ-XXXX` statements using RFC 2119 (`MUST`, `SHALL`, `MUST NOT`) paired with explicit `WHEN / THEN` scenarios.
4. **Non-Functional Requirements**: Quantifiable latency, concurrency, memory, security, and test-coverage (`>80%`) invariants.
5. **Acceptance Criteria**: Binary pass/fail verification checklist mapped 1:1 to `REQ-XXXX` IDs.
6. **Out of Scope**: Explicit negative scope boundaries to prevent agent scope creep during `/conductor:implement`.
7. **Verification Commands**: Exact non-interactive shell commands (`CI=true ...`) required to prove compliance.

## 2. OpenSpec Behavioral Contract Rules (`openspec/specs/<capability>/spec.md`)

1. Use `### Requirement: <Title> (REQ-XXXX)` for every capability requirement.
2. Include at least one normative RFC 2119 keyword (`SHALL`, `MUST`, `SHOULD`, `MAY`) in the requirement summary.
3. Follow every requirement with one or more `#### Scenario:` headers (strictly **4 hashtags**; `### Scenario:` is invalid).
4. Write scenario bodies using **Given / When / Then** (`- **GIVEN** ...`, `- **WHEN** ...`, `- **THEN** ...`).
5. When modifying an existing requirement under `## MODIFIED Requirements`, copy the **entire** requirement block (including all retained scenarios) so no existing behavior is silently dropped on archive.
