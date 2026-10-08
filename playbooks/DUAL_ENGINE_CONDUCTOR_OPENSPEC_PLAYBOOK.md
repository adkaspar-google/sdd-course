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

---

## 6. Human Interaction & The 4-Layer Validation Loop (Software 3.0 & `autoresearch` Pattern)

As Andrej Karpathy observed in his **Software 3.0** and **`autoresearch`** frameworks, moving from casual **"Vibe Coding"** to production **Agentic Engineering** recognizes a fundamental law: **code generation is now virtually free; human verification is the true bottleneck.**

To maximize the speed and safety of the **Generation $\to$ Verification Loop**, this playground enforces **4 Human Interaction Gates** ("Iron Man Suit" controls / "Short Leash") and **4 Automated Validation Layers**:

### A. The 4 Human Interaction Gates & Karpathy's 4 Coding Agent Rules

| Human Control Gate | How You Interact in `Conductor` + `OpenSpec` | Karpathy Agent Rule Enforced |
| :--- | :--- | :--- |
| **1. Interactive Clarification Q&A** (`/conductor:newTrack` & `/opsx:explore`) | Runs inside a **Plan Mode Sandbox** (`policies/conductor.toml` blocks writes outside `conductor/`). The agent asks **3–5 targeted clarifying questions** to surface trade-offs before touching code. | **1. Think Before Coding** (Zero silent assumptions) |
| **2. Spec-First Contract Approval** (`proposal.md`, `spec.md`, `ADR-*.md`) | Like `program.md` in `autoresearch`, the human steers and approves a concise **50-line behavioral contract** (`REQ-0001..REQ-0006` + ADRs in **Lab 01 & Lab 02**) instead of auditing a 2,000-line surprise diff. | **2. Simplicity First** (Minimal surface area & explicit intent) |
| **3. Surgical Scope & Stack Lock** (`## 6. Out of Scope` & `tech-stack.md`) | In **Lab 04**, the human uses the Engineering Scorecard to approve *only* `F-01` (`REQ-0005` bug) while locking `F-02..F-04` in `## 6. Out of Scope`. Any unapproved library triggers a **Tech-Stack Deviation Halt**. | **3. Surgical Changes** (Zero collateral refactoring of adjacent working code) |
| **4. Short-Leash Phase Checkpoints** (`plan.md` & `tasks.md` Batches) | Work is sliced into small phases (**Lab 03**) and **Stacked PR Batches** (**Lab 05**). At each phase end, Conductor pauses for **User Manual Verification** before recording `[checkpoint: <sha>]`. | **4. Goal-Driven Execution & Short Leash** (Fast visual/diff verification + `/conductor:revert`) |

### B. The 4 Automated Validation Layers (`./self_diagnose_all.sh`)

1. **Layer 1 — Static Contract & Schema Validation (`openspec validate --strict` & `self_diagnose.sh`):**
   Deterministically verifies that specifications contain `REQ-XXXX` IDs, normative RFC 2119 keywords (`SHALL`, `MUST`), 4-hashtag `#### Scenario:` (`GIVEN`/`WHEN`/`THEN`), and the 7-Section Conductor `spec.md` anatomy *before* code execution.
2. **Layer 2 — 1-to-1 Requirement-Traceable TDD (`Red` $\to$ `Green` $\to$ `Refactor`):**
   Every requirement (`REQ-0001..REQ-0007`) maps 1-to-1 to a unit test (`test_req0001_...` in **Lab 03**) executed with `CI=true python3 -m unittest`.
3. **Layer 3 — Spec-Drift & Patch Auditing (`/conductor:review` & `/opsx:verify` in Lab 05):**
   Cross-checks code diffs against `openspec/specs/` to catch behavioral regressions (e.g., `get()` mutating FIFO order into LRU in `subpar_change.patch`) and un-specced methods (`put_with_ttl()`).
4. **Layer 4 — Immutable Adversarial Verifier (`chmod -w` Clean-Room Rebuild Test in Lab 06):**
   Directly implements Karpathy's **`autoresearch` immutable evaluator (`prepare.py`)** rule: in **Lab 06**, `self_diagnose.sh` copies the regenerated service into `/tmp/sdd_rebuild_...` alongside an independent adversarial test suite locked read-only with **`chmod -w`**, guaranteeing the agent can never pass by deleting or weakening failing test assertions.

### C. Joel Spolsky's Law of Leaky Abstractions: Why Code Generation Saves Time *Working*, Not Time *Learning*

In his classic 2002 essay [***"The Law of Leaky Abstractions"*** (*Joel on Software*, Nov 11, 2002)](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/), Joel Spolsky stated a universal engineering law:

> **"All non-trivial abstractions, to some degree, are leaky."**
>
> *"The law of leaky abstractions means that whenever somebody comes up with a wizzy new code-generation tool that is supposed to make us all ever-so-efficient, you hear a lot of people saying 'learn how to do it manually first, then use the wizzy tool to save time.' Code generation tools which pretend to abstract out something, like all abstractions, leak, and the only way to deal with the leaks competently is to learn about how the abstractions work and what they are abstracting. **So the abstractions save us time working, but they don't save us time learning.**"*

**Natural-language prompting ("Vibe Coding") is the ultimate leaky abstraction.** When you prompt an agent *"build a rate limiter"* or *"add a distributed lock"*, the prompt abstracts away concurrency, clock monotonicity, failure recovery, and state-machine boundaries. Every single hands-on lab in `SDD-Crash-Course` is designed around a real-world abstraction leak that breaks naive AI-generated code unless pinned down by an explicit **Specification (`REQ-XXXX`)**, **Architecture Decision Record (`ADR-*.md`)**, and **Traceable Unit Test (`test_reqXXXX_*`)**:

| Lab | The High-Level Prompt Abstraction | How the Abstraction Leaks in Production | How SDD + TDD Plugs the Leak |
| :--- | :--- | :--- | :--- |
| **`Lab 01`** | *"Limit each tenant to $N$ requests per window."* | Fixed-window counters allow a $2\times$ burst at window boundaries; concurrent threads race on shared counters; wall-clock jumps corrupt windows. | `ADR-0002` (sliding-window timestamp log), `REQ-0004` (injectable monotonic clock), and `REQ-0005` (`threading.RLock` concurrency test). |
| **`Lab 02`** | *"Acquire a distributed lock with a TTL."* | A paused client (GC pause or network delay $>$ TTL) wakes up after its lock expired and overwrites the new lock holder's storage (**split-brain**). | `REQ-0002` & `ADR-0001`: strictly monotonic 64-bit `fencing_token` that never resets across releases or expirations. |
| **`Lab 03`** | *"Call a remote RPC service just like a local function."* (Spolsky's classic TCP/NFS leak) | When the downstream dependency hangs or fails, naive callers retry in a tight loop and exhaust thread pools across the fleet. | `REQ-0001..0007`: explicit `CLOSED` $\to$ `OPEN` $\to$ `HALF_OPEN` state machine with `half_open_max_calls = 1` single-probe gating. |
| **`Lab 04`** | *"Continuously replenish quota at $r$ tokens/sec."* | Integer truncation (`int(elapsed * rate) == 0`) on sub-quantum polling (`0.4s < 1.0s`) overwrites `last_replenished = now` and starves the bucket forever. | `REQ-0005` & 5-Step Scorecard Track (`F-01`): advance `last_replenished` only by `added / rate` when `added > 0`. |
| **`Lab 05`** | *"Cache key-value pairs up to `max_size`."* | Calling `move_to_end()` inside `get()` silently mutates deterministic FIFO eviction (`REQ-0002`) into LRU; expired TTL keys evict live entries. | `/conductor:review` + `/opsx:verify` spec-diff audit; `REQ-0006` eager+lazy TTL purge before capacity eviction. |
| **`Lab 06`** | *"Natural language is the new source code."* | Ambiguous prose omits duplicate-enrollment idempotency (`REQ-0003`) or FIFO waitlist promotion (`REQ-0004`), and agents weaken tests to pass. | Canonical 8-Section `SPEC.md` (SSOT) + Clean-Room Rebuild Test against read-only (`chmod -w`) `adversarial_tests/`. |

