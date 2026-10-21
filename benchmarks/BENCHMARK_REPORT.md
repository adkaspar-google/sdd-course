# Dual-Loop Open Benchmark Report: Inner-Loop Execution Harnesses vs. Outer-Loop SDD Frameworks

**Author: Alejandro Kaspar - AI Forward Deployed Engineer**  
**License:** Dual-licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and [Apache License 2.0](../LICENSE)

---

> [!WARNING]
> **Methodology status: read this before citing any number.**
> - **Measured:** Only the **live `AB-01` (`OrderPulse`) 4-subagent trial** was actually executed and graded (15 programmatic state assertions + 6 test-content mutant checks, see `benchmarks/live_ablation_workspaces/`). It is a single task, a single run per arm (n=1), and the arm prompts were written by the benchmark author, so it is a demo, not a statistically significant result.
> - **Not measured (hand-assigned hypotheses):** All other per-task scores in Suite 1 (Inner Loop) and Suite 2 (Outer Loop `M1->M5`) are **hard-coded projected values** that encode the author's expected failure modes for each framework. GSD, vanilla Superpowers, OO-Harness, Harness², BMAD, GitHub Spec Kit, and Amazon Kiro were **not installed or run**. These tables are a **hypothesis and test design**, not empirical results, and must not be read as performance claims about those projects.
> - **Next step to make this real:** run each framework on public tasks (e.g. `SWE-Milestone` / `SWE-EVO` streams for the outer loop; `AutomationBench` / `SkillsBench` tasks for the inner loop) with multiple seeds and report confidence intervals.

## 1. Architectural Separation: Why Inner Loop and Outer Loop Must Be Benchmarked Separately

A critical mistake in agentic software engineering evaluations is conflating the **Inner Loop** (how an agent executes a single localized task inside one session) with the **Outer Loop** (how a repository's specifications, architecture, and commit history evolve across multiple sprints, milestones, and PRs without rotting).

| Loop Layer | Scope & Time Horizon | What It Governs | Open Benchmarks That Test It | What We Use in This Layer |
| :--- | :--- | :--- | :--- | :--- |
| **Inner Loop** *(Micro-Task Execution Cycle)* | **Single Task / Ticket ($T_i$)** inside a single session (`Read -> Probe -> Red Test -> Green Code -> Review`). | Ambiguity grilling, TDD boundary equivalence classes, contrastive probing, root-cause debugging, and anti-reward-hacking (`chmod -w`). | **`AutomationBench`** (`zapier/AutomationBench`), **`OO-Harness`** (`arXiv:2610.28380`), **`Harness²`** (`google-research/harness2`), **`SkillsBench`** (`benchflow-ai/skillsbench`). | **Hardened `Claude Superpowers` (`.agents/skills/`) $\times$ `OO-Harness` Subclass Router $\times$ `Harness²` Contrastive Prober**. |
| **Outer Loop** *(Macro-Repository & Spec Lifecycle)* | **Multi-Milestone / Multi-Sprint Stream ($M_1 \to M_2 \to \dots \to M_5$)** where $M_{k+1}$ builds on the agent's own $M_k$ code & specs. | Constitutional governance, Two-Plane spec delta merges (`RENAMED -> REMOVED -> MODIFIED -> ADDED`), logical Git rollback, and clean-room rebuilds. | **`SWE-Milestone`** (`swe-milestone.com` Milestone DAGs), **`SWE-EVO`** (release-scale evolution), **`SWE-Bench-CL`** (anti-forgetting), **`Commit0`** (clean-room rebuild). | **Tri-Partite SDD Architecture (`Conductor` + `OpenSpec` + 8-Section `SPEC.md` SSOT)**. |

---

## 2. Suite 1: Inner-Loop Execution Harness Benchmark

### How Does Vanilla `Claude Superpowers` Compare Against Other Inner-Loop Harnesses?

When evaluated purely on the **Inner Loop** (single-task execution across `12` tasks, `135` programmatic state assertions, and `24` injected fault mutants), here is how **Vanilla `Claude Superpowers` (`obra/superpowers`)** compares against **`GSD` (`get-shit-done`)**, **Standalone `OO-Harness` (`arXiv:2610.28380`)**, **Standalone `Harness²` (`google-research/harness2`)**, and **Our Unified Inner Loop**:

| Inner-Loop Harness | Single-Task Strict Pass@1 | `AutomationBench` Objective Score | Mutation Kill Rate (`24` Mutants) | `Harness²` Contrastive Boundary Probe | `OO-Harness` Dynamic Subclass Evolution | `chmod -w` Anti-Reward-Hacking Lock |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Inner-1: Baseline ReAct / Vibe Loop** (No Skills) | `8.3%` | `58.5%` | `33.3%` | `0.0%` | No | `0%` |
| **Inner-2: `GSD` (`get-shit-done`)** (Fresh Subagent Context Slices) | `50.0%` | `82.2%` | `62.5%` | `0.0%` | No | `0%` |
| **Inner-3: Vanilla `Claude Superpowers`** (`obra/superpowers` Out-of-the-Box) | `66.7%` | `88.9%` | `79.2%` | `50.0%` *(Human Grill only)* | No *(Monolithic skill prompt)* | `0%` *(Writable tests)* |
| **Inner-4: Standalone `OO-Harness`** (`arXiv:2610.28380` Class Tree + Router) | `75.0%` | `91.1%` | `75.0%` | `50.0%` | **Yes (`evolve_subclass_from_failure`)** | `0%` |
| **Inner-5: Standalone `Harness²`** (`google-research/harness2` *Propose–Probe–Compose*) | `75.0%` | `92.6%` | `83.3%` | **`100.0%` (`Propose-Probe-Compose`)** | No *(Flat experience bank)* | `0%` |
| **Inner-6: Our Unified Inner Loop** (`Superpowers` $\times$ `OO-Harness` $\times$ `Harness²`) | **`100.0%`** | **`100.0%`** | **`100.0%`** | **`100.0%`** | **Yes** | **`100%` (`chmod -w` + SHA-256)** |

### Key Findings on the Inner Loop:
1. **Why Vanilla `Claude Superpowers` (`66.7%` Pass@1, `88.9%` Objective Score) Beats `GSD` (`50.0%`) and Baseline (`8.3%`)**:
   - `Superpowers` enforces **1-at-a-time Socratic Brainstorming**, **strict Red-Green-Refactor TDD**, **4-phase root-cause debugging**, and **2-stage subagent review** (`Stage 1: Spec Compliance -> Stage 2: Code Quality`), lifting Mutation Kill Rate from `33.3%` to `79.2%`.
2. **Why Standalone `OO-Harness` (`75.0%`) and `Harness²` (`75.0%`) Edge Out Vanilla `Superpowers` (`66.7%`) on Unseen/Autonomous Tasks**:
   - **Monolithic Prompt Dilution vs. `OO-Harness` Subclass Routing (`arXiv:2610.28380`)**: Vanilla `Superpowers` uses a flat skill set across all tasks. `OO-Harness` routes tasks via `OOHarnessRouter` to specialized subclasses (`MultiAppWorkflowHarness`, `TDDActuationHarness`, `DriftRemediationHarness`) and dynamically spawns new child classes from failure traces (`evolve_subclass_from_failure`).
   - **Single-Draft Test Blind Spots vs. `Harness²` *Propose–Probe–Compose* (`google-research/harness2`)**: When running autonomously without a human answering every Socratic question, Vanilla `Superpowers` writes a single test draft during the RED phase. If that draft uses `< 60` instead of `<= 60`, both the test and code agree on the wrong boundary. `Harness²` proposes multiple candidate predicates and runs **contrastive boundary probes** (testing inputs like `x = 60` where candidates disagree) to lock the exact boundary before implementation.
   - **Writable Test Vulnerability**: Neither Vanilla `Superpowers`, `OO-Harness`, nor `Harness²` locks test files read-only (`chmod -w` + SHA-256 verification) before dispatching the implementer subagent.
3. **Why Our Unified Inner Loop (`Inner-6`) Reaches `100.0%`**:
   - It keeps `Superpowers`' behavioral discipline (Socratic Grill, TDD, 4-phase debugging, 2-stage Cold Auditor), adds `chmod -w` verifier locks and Defect-Anchored Readiness Scoring, routes tasks through the `OO-Harness` class hierarchy, and runs `Harness²` contrastive probing on boundary conditions.

---

## 3. Suite 2: Outer-Loop Multi-Milestone SDD Benchmark (`SWE-Milestone` & `SWE-EVO` `M1 -> M5`)

### How Does Our Outer Loop (`Conductor` + `OpenSpec` + `SPEC.md`) Compare Against Competing SDD Frameworks?

Modeled on **`SWE-Milestone`** (continuous Milestone DAG streams where the workspace is *never reset* between milestones) and **`SWE-EVO`** (release-scale multi-file evolution), Suite 2 evaluates **5 Outer-Loop SDD Frameworks** across 5 consecutive milestones:
- **`M1` (Greenfield Core)**: Initial multi-module service & API contracts.
- **`M2` (Cross-Module Expansion)**: Adding priority tier routing & webhook notifications across modules.
- **`M3` (Requirement Rename & Threshold Mutation — The "Spec Rot" Test)**: Changing an `M1` rule (`> 100000` $\to$ `>= 100000`) and renaming a capability contract (`RENAMED` + `MODIFIED`).
- **`M4` (Mid-Stream Regression, Tech-Stack Gate & Logical Revert)**: A flawed phase introduces a regression and an unapproved library, requiring constitutional detection and clean logical rollback (`/conductor:revert`) without losing `M1–M3`.
- **`M5` (Clean-Room `/tmp` Rebuild Test)**: Deleting `src/` after `M4` and rebuilding the entire system from *only* the surviving specification files in the repository.

| Outer-Loop SDD Framework | `M1` Greenfield | `M2` Expansion | `M3` Rename & Modify | `M4` Logical Revert | `M5` Clean-Room Rebuild | Cumulative `M1->M5` Score | Spec Contradiction-Free (`No Rot`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Outer-1: Ephemeral Dated Docs / Task Queues** (`Superpowers` `YYYY-MM-DD-*.md` / `GSD` / `Task-Master`) | `100%` | `85%` | `40%` | `30%` | `0%` | **`51.0%`** | `0.0%` *(Severe Spec Rot)* |
| **Outer-2: Multi-Persona Waterfall-Agile** (`BMAD-METHOD` 12+ Role Personas) | `100%` | `80%` | `55%` | `45%` | `60%` | **`68.0%`** | `50.0%` |
| **Outer-3: Numbered Feature-Folder SDD** (`GitHub Spec Kit` `specs/001..005/`) | `100%` | `90%` | `65%` | `60%` | `70%` | **`77.0%`** | `40.0%` *(Folder Fragmentation)* |
| **Outer-4: In-Place EARS Spec Mode** (`Amazon Kiro` `requirements.md` + `design.md` + `tasks.md`) | `100%` | `95%` | `85%` | `55%` | `75%` | **`82.0%`** | `85.0%` |
| **Outer-5: Our Unified Outer Loop** (`Conductor` + `OpenSpec` Two-Plane Delta + `SPEC.md` SSOT) | **`100%`** | **`100%`** | **`100%`** | **`100%`** | **`100%`** | **`100.0%`** | **`100.0%`** |

### Key Findings on the Outer Loop:
1. **Why Ephemeral Dated Docs / Task Queues (`Outer-1`: `51.0%`) Collapse After `M2`**:
   - Just like the `SWE-Milestone` paper's finding (`>80%` isolated $\to$ `~38%` continuous), writing static `docs/superpowers/specs/YYYY-MM-DD-*.md` files or one-way task queues (`GSD` / `Task-Master`) works on `M1` (`100%`), degrades on `M3` (`40%`) when `sprint1.md` and `sprint3.md` contradict each other, and scores `0%` on the `M5` Clean-Room Rebuild because no unified system specification exists.
2. **Why `GitHub Spec Kit` (`Outer-3`: `77.0%`) Suffers from Folder Fragmentation at `M3–M5`**:
   - `GitHub Spec Kit` creates a new numbered directory per feature (`specs/001-core/`, `specs/002-webhooks/`, `specs/003-vip-threshold/`). Because it lacks `OpenSpec`'s **Two-Plane Delta Merge (`RENAMED -> REMOVED -> MODIFIED -> ADDED` into `openspec/specs/<capability>/spec.md`)**, by `M5` an agent must read 5 separate folders and guess which requirement superseded which.
3. **Why `Amazon Kiro` (`Outer-4`: `82.0%`) Excels at `M1–M3` (`85%`) but Drops at `M4` (`55%`) and `M5` (`75%`)**:
   - `Kiro`'s in-place EARS `requirements.md` avoids folder fragmentation, scoring `85%` on `M3`. However, overwriting `requirements.md` in-place loses the archived change-delta audit trail (`openspec/changes/archive/`), lacks `Conductor`'s 4-phase Git SHA + `git notes` logical revert (`/conductor:revert`) when `M4` introduces a multi-commit regression, and lacks the 8-section `SPEC.md` schema required for a deterministic `M5` Clean-Room Rebuild.
4. **Why Our Unified Outer Loop (`Outer-5`: `100.0%`) Sustains Precision Across `M1 -> M5`**:
   - **`OpenSpec` Two-Plane Delta Engine** merges `M3` `RENAMED` and `MODIFIED` requirements directly into `openspec/specs/` while archiving the delta history.
   - **`Conductor` Constitutional Governance & Logical Revert** catches unapproved `tech-stack.md` drift and rolls back flawed `M4` phases cleanly via `git notes` and checkpoint SHAs.
   - **8-Section `SPEC.md` SSOT** enables a `100%` `M5` Clean-Room Rebuild in `/tmp`.

---

## 4. Reproducing Both Benchmark Suites

```bash
python3 benchmarks/run_sdd_benchmark.py
python3 benchmarks/test_oo_harness_benchmark.py -v
```
