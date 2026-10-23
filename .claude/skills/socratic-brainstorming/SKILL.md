---
name: socratic-brainstorming
description: Enforces single-question Socratic grilling, 2-3 architectural trade-off proposals (ADRs), and incremental validation wired directly into OpenSpec and Conductor specs rather than ephemeral date-stamped files.
---

# Socratic Brainstorming & Design Validation (`socratic-brainstorming`)

Combine the inner-loop behavioral discipline of **Claude Superpowers (`brainstorming`)** with the outer-loop persistent specification architecture of **OpenSpec (`openspec/specs/`)** and **Conductor (`conductor/tracks/`)**.

## 1. Mandatory Inner-Loop Discipline ("The Grill")

1. **Context Gathering First**: Read `conductor/index.md`, `conductor/tech-stack.md`, and any existing baseline capability specs in `openspec/specs/<capability>/spec.md` before asking questions.
2. **Single-Question Policy (No Question Dumps)**: Ask clarifying questions **one at a time** (or at most 3 tightly focused edge-case questions `Q1..Q3` in batch CLI mode). Focus strictly on behavioral boundaries, error handling, and scope limits.
3. **Propose 2–3 Architectural Alternatives**: Before locking in a non-trivial design choice (e.g., ID generation strategy, tag normalization, state storage), present 2–3 concrete options with explicit pros/cons and record the chosen option as an **Architecture Decision Record (`ADR-XXXX`)**.
4. **Incremental Validation (200–300 Word Blocks)**: Present design sections in concise, digestible blocks and pause for human approval before generating implementation tasks.
5. **Ruthless Simplification (YAGNI)**: Actively strip speculative features and lock rejected ideas inside `## 6. Out of Scope`.

## 2. Outer-Loop Destination Rule (No Ephemeral Date-Stamped Graveyards)

- **NEVER** write standalone chronological design snapshots like `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` that rot after the PR merges.
- **ALWAYS** route validated designs directly into the living Two-Plane Specification Architecture:
  1. **Capability Delta Contract**: `openspec/changes/<change_id>/specs/<capability>/spec.md` (`## ADDED`, `## MODIFIED`, `## REMOVED`, `## RENAMED Requirements` with RFC 2119 keywords and 4-hashtag `#### Scenario:` blocks).
  2. **Technical Rationale & ADRs**: `openspec/changes/<change_id>/design.md` (`ADR-XXXX`).
  3. **7-Section Track Specification**: `conductor/tracks/<track_id>/spec.md`.
