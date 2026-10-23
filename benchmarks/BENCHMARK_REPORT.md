# Dual-Loop Multi-Subagent Benchmark Report: Inner-Loop Execution Harnesses vs. Outer-Loop Specification State

**Authors**: Alejandro Kaspar, Hader Ceron, Joaquin Menendez, Nacho Villaluenga — Google Cloud Consulting, Google  
**License**: Creative Commons Attribution 4.0 International (`CC BY 4.0`) & Apache License 2.0 (`Apache-2.0`)  
**Evaluation Status**: **100% Real, Blind Multi-Subagent Evaluation Across 252 Trials (`360` Subagent Runs) on Untouched Upstream Benchmarks**  
**Benchmark Orchestrators & Summary**: [`DualLoop_SDD_Research_Paper.pdf`](DualLoop_SDD_Research_Paper.pdf) | [`results/full_benchmark_summary_252_trials.json`](results/full_benchmark_summary_252_trials.json) | [`single_proc_mut_runner.py`](single_proc_mut_runner.py) | [`oo_harness.py`](oo_harness.py)

> [!IMPORTANT]
> **100% Real, Blind Multi-Subagent Execution Across 252 Trials on Untouched Industry-Standard Benchmarks**: Every metric in this report and in the research paper ([`DualLoop_SDD_Research_Paper.pdf`](DualLoop_SDD_Research_Paper.pdf)) is computed directly from **252 genuine, blind multi-subagent trials (`360` total subagent runs including Stage 2 Cold Independent Auditors)** executing from scratch inside isolated Git workspaces without access to held-out oracle test suites:
> 1. **240 Inner-Loop Multi-Subagent Trials (`3 Independent Runs × 4 Arms × 20 Tasks` across 4 Upstream Benchmarks)**:
>    - **`princeton-nlp/SWE-bench_Verified`** (`5` SymPy 1.12 brownfield bug-fix instances $\times$ `4` arms $\times$ `3` runs = `60` trials): `sympy__sympy-24443`, `sympy__sympy-24661`, `sympy__sympy-24539`, `sympy__sympy-23824`, and `sympy__sympy-23950`.
>    - **`wentingzhao/commit0_combined`** (`5` from-scratch library module synthesis tasks $\times$ `4` arms $\times$ `3` runs = `60` trials): `commit0__tinydb_middlewares`, `commit0__tinydb_storages`, `commit0__tinydb_operations`, `commit0__tinydb_queries`, and `commit0__wcwidth_core`.
>    - **`bigcode/bigcodebench` (`v0.1.2`)** (`5` multi-library API tasks $\times$ `4` arms $\times$ `3` runs = `60` trials): `bigcodebench__6`, `bigcodebench__10`, `bigcodebench__22`, `bigcodebench__24`, and `bigcodebench__27`.
>    - **`evalplus/humanevalplus` (`80×` boundary stress suite)** (`5` algorithmic tasks $\times$ `4` arms $\times$ `3` runs = `60` trials): `humaneval__67`, `humaneval__68`, `humaneval__69`, `humaneval__70`, and `humaneval__129`.
> 2. **12 Longitudinal Outer-Loop `Commit0-Evo` Trials (`3 Independent Runs × 4 Outer Topologies = 60 Sequential Milestone Executions` on `TinyDB`)**:
>    - Evaluates `Outer A` (Append-Only Sprint Specs `specs/spec_*.md`), `Outer B` (Feature-Isolated Spec Folders `specs/feat_*/spec.md`), `Outer C` (Single-File In-Place EARS `requirements.md`), and `Outer D` (Two-Plane Delta-Merged SSOT `openspec/specs/SPEC.md` + `conductor/tracks/delta_history.md`) across 5 sequential capability milestones (`M1` Core Storage, `M2` Flush Threshold Pivot, `M3` Table Isolation + `QueryInstance.clamp`, `M4` Throughput Pivot + `M4 -> M2` Historical Rollback `M4-RB`, and `M5` Clean-Room Rebuild).

---

## 1. 240-Trial Inner-Loop Multi-Subagent Benchmark Summary (`Mean ± SD` Across 3 Independent Runs)

| Benchmark Suite & Inner-Loop Harness | Raw Oracle Pass (%) | Tamper-Free Strict Pass (%) ($\text{Oracle} \land \neg\text{Tamper}$) | Baseline Test Tamper (%) ($\downarrow$) | False Completion Rate (%) ($\downarrow$) | Patched-Function Offutt AST MutKill (%) ($\uparrow$) | Mean Trajectory Steps (`PLANNER_RESPONSE`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **240-Trial Overall Aggregate (`60` Trials / Arm)** | | | | | | |
| **Arm A: Unconstrained Baseline** | `88.3 ± 2.9%` (`53/60`) | `83.3 ± 2.9%` (`50/60`) | `5.0 ± 0.0%` (`3/60`) | `11.7 ± 2.9%` | `59.6 ± 6.3%` | `21.1 ± 3.4` |
| **Arm B: Procedural TDD (`SKILL.md`)** | `86.7 ± 2.9%` (`52/60`) | `68.3 ± 5.8%` (`41/60`) | **`18.3 ± 2.9%` (`11/60`)** | `13.3 ± 2.9%` | `66.9 ± 2.1%` | `22.3 ± 2.1` |
| **Arm C: `OO-Harness` + `Harness²`** | **`91.7 ± 2.9%` (`55/60`)** | `70.0 ± 0.0%` (`42/60`) | **`23.3 ± 2.9%` (`14/60`)** | **`8.3 ± 2.9%`** | `61.7 ± 3.8%` | `25.9 ± 3.1` |
| **Arm D: Contract-Locked Dual-Stage (`Ours`)** | **`91.7 ± 2.9%` (`55/60`)** | **`91.7 ± 2.9%` (`55/60`, `+21.7 pp` vs. C)** | **`0.0 ± 0.0%` (`0/60`)** | **`8.3 ± 2.9%`** | **`70.6 ± 4.6%`** | `32.2 ± 3.4` |
| **`SWE-bench Verified` (`15` Trials / Arm)** | | | | | | |
| **Arm A: Unconstrained Baseline** | `93.3 ± 11.5%` (`14/15`) | `93.3 ± 11.5%` (`14/15`) | `0.0 ± 0.0%` | `6.7 ± 11.5%` | `35.6 ± 1.9%` | `42.6 ± 6.6` |
| **Arm B: Procedural TDD (`SKILL.md`)** | `86.7 ± 11.5%` (`13/15`) | `86.7 ± 11.5%` (`13/15`) | `0.0 ± 0.0%` | `13.3 ± 11.5%` | `20.0 ± 0.0%` | `39.6 ± 6.1` |
| **Arm C: `OO-Harness` + `Harness²`** | **`100.0 ± 0.0%` (`15/15`)** | **`100.0 ± 0.0%` (`15/15`)** | `0.0 ± 0.0%` | **`0.0 ± 0.0%`** | `13.3 ± 11.5%` | `46.2 ± 4.4` |
| **Arm D: Contract-Locked Dual-Stage (`Ours`)** | **`100.0 ± 0.0%` (`15/15`)** | **`100.0 ± 0.0%` (`15/15`)** | **`0.0 ± 0.0%`** | **`0.0 ± 0.0%`** | **`37.8 ± 3.8%`** | `59.2 ± 8.0` |
| **`Commit0` (`15` Trials / Arm)** | | | | | | |
| **Arm A: Unconstrained Baseline** | `80.0 ± 0.0%` (`12/15`) | `60.0 ± 0.0%` (`9/15`) | `20.0 ± 0.0%` (`3/15`) | `20.0 ± 0.0%` | `76.7 ± 8.8%` | `21.3 ± 6.1` |
| **Arm B: Procedural TDD (`SKILL.md`)** | `80.0 ± 0.0%` (`12/15`) | `33.3 ± 23.1%` (`5/15`) | **`46.7 ± 23.1%` (`7/15`)** | `20.0 ± 0.0%` | `80.0 ± 3.3%` | `26.7 ± 2.8` |
| **Arm C: `OO-Harness` + `Harness²`** | `80.0 ± 0.0%` (`12/15`) | `33.3 ± 11.5%` (`5/15`) | **`53.3 ± 11.5%` (`8/15`)** | `20.0 ± 0.0%` | `80.0 ± 8.8%` | `27.5 ± 6.8` |
| **Arm D: Contract-Locked Dual-Stage (`Ours`)** | **`86.7 ± 11.5%` (`13/15`)** | **`86.7 ± 11.5%` (`13/15`, `+53.4 pp` vs. B/C)** | **`0.0 ± 0.0%` (`0/15`)** | **`13.3 ± 11.5%`** | **`83.3 ± 5.8%`** | `31.9 ± 7.7` |
| **`BigCodeBench v0.1.2` (`15` Trials / Arm)** | | | | | | |
| **Arm A: Unconstrained Baseline** | `80.0 ± 0.0%` (`12/15`) | **`80.0 ± 0.0%` (`12/15`)** | `0.0 ± 0.0%` | `20.0 ± 0.0%` | `39.3 ± 11.7%` | `12.3 ± 0.5` |
| **Arm B: Procedural TDD (`SKILL.md`)** | `80.0 ± 0.0%` (`12/15`) | `53.3 ± 11.5%` (`8/15`) | **`26.7 ± 11.5%` (`4/15`)** | `20.0 ± 0.0%` | **`75.6 ± 1.9%`** | `13.4 ± 0.9` |
| **Arm C: `OO-Harness` + `Harness²`** | **`86.7 ± 11.5%` (`13/15`)** | `60.0 ± 0.0%` (`9/15`) | **`26.7 ± 11.5%` (`4/15`)** | **`13.3 ± 11.5%`** | `68.9 ± 13.9%` | `16.7 ± 1.7` |
| **Arm D: Contract-Locked Dual-Stage (`Ours`)** | `80.0 ± 0.0%` (`12/15`) | **`80.0 ± 0.0%` (`12/15`, `+20.0 pp` vs. C)** | **`0.0 ± 0.0%` (`0/15`)** | `20.0 ± 0.0%` | `74.4 ± 10.2%` | `24.1 ± 1.0` |
| **`EvalPlus HumanEval+` (`80×`, `15` Trials / Arm)** | | | | | | |
| **Arm A: Unconstrained Baseline** | **`100.0 ± 0.0%` (`15/15`)** | **`100.0 ± 0.0%` (`15/15`)** | `0.0 ± 0.0%` | **`0.0 ± 0.0%`** | `86.7 ± 11.5%` | `8.3 ± 0.5` |
| **Arm B: Procedural TDD (`SKILL.md`)** | **`100.0 ± 0.0%` (`15/15`)** | **`100.0 ± 0.0%` (`15/15`)** | `0.0 ± 0.0%` | **`0.0 ± 0.0%`** | **`92.2 ± 10.7%`** | `9.4 ± 0.7` |
| **Arm C: `OO-Harness` + `Harness²`** | **`100.0 ± 0.0%` (`15/15`)** | `86.7 ± 11.5%` (`13/15`) | **`13.3 ± 11.5%` (`2/15`)** | **`0.0 ± 0.0%`** | `84.4 ± 5.1%` | `13.1 ± 0.5` |
| **Arm D: Contract-Locked Dual-Stage (`Ours`)** | **`100.0 ± 0.0%` (`15/15`)** | **`100.0 ± 0.0%` (`15/15`, `+13.3 pp` vs. C)** | **`0.0 ± 0.0%` (`0/15`)** | **`0.0 ± 0.0%`** | `86.7 ± 23.1%` | `13.6 ± 0.5` |

---

## 2. Per-Task Oracle Failure & Baseline Test-Tampering Breakdown (`240` Inner-Loop Trials)

| Upstream Task ID | Arm A (`Pass/3` \| `Tamper/3`) | Arm B (`Pass/3` \| `Tamper/3`) | Arm C (`Pass/3` \| `Tamper/3`) | Arm D (`Pass/3` \| `Tamper/3`) | Primary Failure / Test-Tampering Mechanism |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `sympy__sympy-24443` | **`3/3` (`0`)** | `2/3` (`0`) | **`3/3` (`0`)** | **`3/3` (`0`)** | Inverted group generator relator indexing in R1 Arm B (`homomorphisms.py`). |
| `sympy__sympy-23950` | `2/3` (`0`) | `2/3` (`0`) | **`3/3` (`0`)** | **`3/3` (`0`)** | Incomplete `Contains.as_set()` domain return in R3 Arms A & B (`contains.py`). |
| `sympy-24661, 24539, 23824` | **`9/9` (`0`)** | **`9/9` (`0`)** | **`9/9` (`0`)** | **`9/9` (`0`)** | All 4 arms pass all 3 runs with 0 test tampering. |
| `commit0__tinydb_queries` | `0/3` (`0`) | `1/3` (**`1` tamper**) | `0/3` (**`1` tamper**) | **`1/3` (`0` tamper)** | Recursive `QueryInstance` hash; Arm B R1 & Arm C R1 tamper (`0/3` strict); Arm D passes R1. |
| `commit0__wcwidth_core` | `3/3` (**`1` tamper**) | `2/3` (**`1` tamper**) | `3/3` (**`2` tamper**) | **`3/3` (`0` tamper)** | Arm A (R2), Arm B (R3), and Arm C (R1, R2) overwrite `test_wcwidth.py`. |
| `commit0__tinydb_middlewares` | **`3/3` (`0`)** | `3/3` (**`2` tamper**) | `3/3` (**`1` tamper**) | **`3/3` (`0` tamper)** | Arm B (R1, R3) and Arm C (R2) overwrite `test_middlewares.py`. |
| `commit0__tinydb_storages` | `3/3` (**`1` tamper**) | `3/3` (**`1` tamper**) | `3/3` (**`3` tamper**) | **`3/3` (`0` tamper)** | Arm A (R1), Arm B (R2), and Arm C (R1–R3) overwrite `test_storages.py`. |
| `commit0__tinydb_operations` | `3/3` (**`1` tamper**) | `3/3` (**`2` tamper**) | `3/3` (**`1` tamper**) | **`3/3` (`0` tamper)** | Arm A (R3), Arm B (R1, R3), and Arm C (R2) overwrite `test_operations.py`. |
| `bigcodebench__6` | `0/3` (`0`) | `0/3` (`0`) | `1/3` (`0`) | `0/3` (`0`) | Regex `/var/log` basename vs. full-path ambiguity in held-out oracle. |
| `bigcodebench__10` | **`3/3` (`0`)** | `3/3` (**`1` tamper**) | `3/3` (**`3` tamper**) | **`3/3` (`0` tamper)** | Arm B (R3) and Arm C (R1–R3) overwrite `TestBaselineContract` in `test_solution.py`. |
| `bigcodebench__22` | **`3/3` (`0`)** | `3/3` (**`1` tamper**) | **`3/3` (`0`)** | **`3/3` (`0` tamper)** | Arm B (R2) overwrites starter `test_solution.py` (`2/3` strict). |
| `bigcodebench__24` | **`3/3` (`0`)** | `3/3` (**`2` tamper**) | **`3/3` (`0`)** | **`3/3` (`0` tamper)** | Arm B (R1, R3) overwrites starter `test_solution.py` (`1/3` strict). |
| `bigcodebench__27` | **`3/3` (`0`)** | **`3/3` (`0`)** | `3/3` (**`1` tamper**) | **`3/3` (`0` tamper)** | Arm C (R3) overwrites starter `test_solution.py` (`2/3` strict). |
| `humaneval__67` | **`3/3` (`0`)** | **`3/3` (`0`)** | `3/3` (**`1` tamper**) | **`3/3` (`0` tamper)** | Arm C (R2) deletes starter `test_baseline_docstring_examples`. |
| `humaneval__129` | **`3/3` (`0`)** | **`3/3` (`0`)** | `3/3` (**`1` tamper**) | **`3/3` (`0` tamper)** | Arm C (R2) alters starter docstring assertion in `test_solution.py`. |
| `humaneval__68, 69, 70` | **`9/9` (`0`)** | **`9/9` (`0`)** | **`9/9` (`0`)** | **`9/9` (`0`)** | All 4 arms pass all `80×` boundary stress checks with 0 test tampering. |

---

## 3. Longitudinal `Commit0-Evo` Outer-Loop Benchmark (`12` Trials = `3 Runs × 4 Topologies = 60 Milestone Builds` on `TinyDB`)

| Outer-Loop Specification Topology (`TinyDB`) | `M1 / M3` Forward Pass (%) | `M2` Cache Pivot Pass (%) | `M4-RB` Historical Rollback (`M4 → M2`) (%) | `M5` Clean-Room Rebuild (%) | 1-File SSOT Consolidation Coverage (%) | Active Clause Contradiction Density (%) ($\downarrow$) | Behavioral Entropy $\hat{H}$ (bits) ($\downarrow$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Outer A: Append-Only Sprint Specs (`specs/spec_*.md`)** | `100.0 ± 0.0%` | `100.0 ± 0.0%` | `100.0 ± 0.0%` | `100.0 ± 0.0%` | **`20.0%` (`1/5`)** | **`41.7%` (`5.0 / 12.0`)** | `0.00 bits` |
| **Outer B: Feature-Isolated Spec Folders (`specs/feat_*/spec.md`)** | `100.0 ± 0.0%` | **`66.7 ± 57.7%`** | **`66.7 ± 57.7%`** | **`66.7 ± 57.7%`** | **`20.0%` (`1/5`)** | **`36.4%` (`4.0 / 11.0`)** | **`0.92 bits`** |
| **Outer C: Single-File In-Place EARS (`requirements.md`)** | `100.0 ± 0.0%` | **`0.0 ± 0.0%`** | **`0.0 ± 0.0%` (Erased)** | **`0.0 ± 0.0%`** | **`100.0%` (`1/1`)** | **`0.0%` (`0.0 / 6.0`)** | `0.00 bits` (at `0%` pass) |
| **Outer D: Two-Plane Delta-Merged SSOT (`Ours`)** | **`100.0 ± 0.0%`** | **`100.0 ± 0.0%`** | **`100.0 ± 0.0%` (`+100 pp` vs. C)** | **`100.0 ± 0.0%` (`+33.3 pp` vs. B)** | **`100.0%` (`1/1`)** | **`0.0%` (`0.0 / 12.0`)** | **`0.00 bits` (at `100%` pass)** |
