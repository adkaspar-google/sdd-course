---
description: Run 1-at-a-time Socratic Grilling (@socratic-brainstorming) and author a 7-Section Spec + OpenSpec REQ-XXXX Delta.
---

Load and follow `.agents/skills/socratic-brainstorming/SKILL.md` and `.agents/skills/writing-arch-specs/SKILL.md`:
1. Inspect the active codebase and `openspec/specs/` in read-only mode.
2. Ask clarifying questions **one at a time** regarding edge cases and boundary conditions (`$ARGUMENTS`).
3. Propose 2–3 `ADR-XXXX` options with trade-offs.
4. Once approved, write the `REQ-XXXX` contract and run `python3 bin/sdd-harness boundary-probe --spec-file <spec.md>` to extract `(c-1, c, c+1)` boundary triples.
