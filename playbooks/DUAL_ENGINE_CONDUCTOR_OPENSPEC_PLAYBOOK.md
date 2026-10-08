# Dual-Engine Engineering Playbook: Context-Driven & Spec-Driven Development with Conductor + OpenSpec

> **Purpose:** Complete practitioner playbook for combining **Conductor** (Context-Driven Development & Phased TDD Orchestration), **OpenSpec** (Capability Contracts & Delta Algebra), **Dedicated Spec Skills (`@writing-arch-specs`)**, and **`SPEC.md` (Single Source of Truth)**.

---

## 1. The Core Synergy: CDD + SDD + Elephant-Goldfish Memory

Modern agentic engineering solves the **"Vibe Coding Amnesia Loop"** by separating **long-term architectural memory ("The Elephant")** from **focused, stateless task execution ("The Goldfish")**:

| Dimension | Ad-Hoc Prompting ("Vibe Coding") | Context-Driven Development (CDD — Conductor) | Spec-Driven Development (SDD — OpenSpec) | **Combined Dual-Engine Approach** |
| :--- | :--- | :--- | :--- | :--- |
| **Memory Role** | Ephemeral chat window (rots after 10 turns) | **Repository Constitution:** `conductor/product.md`, `tech-stack.md`, `workflow.md`, `code_styleguides/` | **System-Oriented Specs ("The Elephant"):** `openspec/specs/<cap>/spec.md` & `SPEC.md` | **Task-Oriented Execution ("The Goldfish"):** `conductor/tracks/<id>/plan.md` & `openspec/changes/<id>/tasks.md` |
| **Drift Risk** | **Critical** (Silent hallucinations & regressions) | **Low** (Locked to approved stack & repo rules) | **Very Low** (Constrained by `SHALL`/`MUST` & Gherkin) | **Near Zero** (Enforced by `openspec validate --strict`, TDD, & `/conductor:review`) |
| **Testing** | Written after the fact (sycophantic self-testing) | Enforces `>80%` coverage & test-per-file gates | Compiles `#### Scenario:` (`WHEN`/`THEN`) into tests | **Strict Red-Green-Refactor TDD + Adversarial Agent Isolation** |

---

## 2. Living Guardrails: Wiring Dedicated Spec Skills & OpenSpec into Conductor

You **never** need to re-run `/conductor:setup` to add new rules or connect a custom spec-writing skill. Because Conductor re-reads `conductor/index.md` and `conductor/workflow.md` at the start of every `/conductor:newTrack`, `/conductor:implement`, and `/conductor:review` invocation, you simply edit two Markdown files in Git:

### 1. `conductor/workflow.md` (Track Specification Policy)
```markdown
### 2. Track Specification Policy (Dual-Engine CDD + SDD Handshake)
- When executing `/conductor:newTrack`, conduct the interactive interview to clarify scope and edge cases.
- Upon user confirmation of questioning completion, the agent MUST invoke `@writing-arch-specs`
  (`.agents/skills/writing-arch-specs/SKILL.md`) and align with `openspec/specs/` to construct `spec.md`.
- All specifications MUST adhere to the 7-Section Architecture Spec Anatomy:
  1. Executive Summary, Legacy Diagnosis & Objective
  2. Environment Prerequisites, Dependencies & Tech-Stack Lock
  3. Technical Contracts, Schemas & Architecture
  4. Concrete Deliverables & Target Files
  5. Verification Gates & Acceptance Criteria (RFC 2119 SHALL/MUST + 4-Hashtag Gherkin WHEN/THEN)
  6. Cost, Concurrency Trade-Offs & Rollback Safeguards
  7. Explicit 'Out of Scope' Boundaries
```

### 2. `conductor/index.md` (Capabilities Handshake)
```markdown
## Capabilities & Specifications
- [Writing Architecture Specs Skill](../.agents/skills/writing-arch-specs/SKILL.md)
- [OpenSpec Canonical Specifications](../openspec/specs/)
```

---

## 3. The 5-Step Brownfield Refactoring Workflow (Lab 04 Pattern)

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer / Lead
    participant Scorecard as Architecture Scorecard (scorecard.md)
    participant Cond as Conductor Engine
    participant SpecSkill as @writing-arch-specs + OpenSpec
    participant Codebase as Target Codebase

    Note over Dev, Scorecard: Step 1 & 2: Assessment & Go/No-Go Decision
    Dev->>Scorecard: 1. Inspect Domain Findings & Drift Violations
    Dev->>Scorecard: 2. Mark ACCEPTED_FOR_REFACTOR, DEFERRED, or REJECTED

    Note over Dev, SpecSkill: Step 3: Dual-Engine Specification & Planning
    Dev->>Cond: 3a. Run /conductor:newTrack
    Cond-->>Dev: Interactive Q&A (clarify edge cases & bounds)
    Cond->>SpecSkill: 3b. Draft 7-Section spec.md + OpenSpec delta + TDD plan.md
    Dev->>Cond: Approve spec.md & plan.md

    Note over Cond, Codebase: Step 4: Phased TDD Implementation
    Dev->>Cond: 4. Run /conductor:implement
    loop Every Task in plan.md
        Cond->>Codebase: Write Failing Test (Red) -> Minimal Code (Green) -> Refactor
        Cond->>Codebase: Verify >80% coverage + Tech-Stack Lock + Atomic Commit & git notes
    end

    Note over Cond, Dev: Step 5: Multi-Axis Review & Archive
    Dev->>Cond: 5. Run /conductor:review + /opsx:verify -> /opsx:archive
```

---

## 4. Stacked Multi-PR Workflows (`git` / `jj`) & The Dedicated Archive PR `N+1` (Lab 05 Pattern)

When a feature is too large for a single Pull Request (`> 400` LOC):
1. **Keep 1 OpenSpec Change Folder (`1 Change = 1 Feature`):** Never create separate change folders per PR.
2. **Batch `tasks.md` by PR:** Group tasks under `## Batch 1: Core Schema (PR 1)`, `## Batch 2: Service Logic (PR 2)`, `## Batch 3: E2E Tests (PR 3)`.
3. **CL/PR-Scoped Task Checkmarks:** In PR 1, mark **only** Batch 1 tasks `- [x]` after their tests pass in PR 1; leave Batch 2 and Batch 3 unchecked `- [ ]`.
4. **Dedicated Archive PR `N+1`:** Never run `/opsx:archive` inside PR 1, PR 2, or PR 3 (moving `openspec/changes/<id>/` to `archive/` mid-stack breaks downstream stacked branches!). Once all code PRs merge, open a zero-code **PR `N+1`** that runs `/opsx:archive <id>`.

---

## 5. The 5 Mandatory Security & Integrity Guardrails

1. **Mandatory Human-in-the-Loop (HITL) Plan Approval:** Never execute `/opsx:apply` or `/conductor:implement` without first reviewing and approving the target file list, `spec.md`, and `plan.md`/`tasks.md`.
2. **Indirect Prompt Injection Defense on `tasks.md`:** Treat workspace `tasks.md` and `proposal.md` files in shared repos as untrusted inputs; reject any task directive attempting unauthorized network calls, credential exfiltration, or file deletions outside the repo.
3. **Strict Separation of Design and Implementation:** Never modify application source code (`src/`) or check off `- [x]` in `tasks.md` during Proposal or Design phases (`/opsx:explore`, `/opsx:new`, `/opsx:ff`, `/conductor:newTrack`).
4. **Truthful Same-PR Task Accounting:** Mark a task `- [x]` **only** after its implementation code and passing tests are verified in the current PR/CL—never speculatively or for follow-up PRs.
5. **VCS Move Provenance (`git mv` / `hg mv`):** When archiving changes into `openspec/changes/archive/YYYY-MM-DD-<id>/`, preserve Git rename history so reviewers see a clean move diff rather than a file deletion + creation.
