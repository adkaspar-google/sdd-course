# Dual-Loop Spec-Driven Development & Contract-Locked Agentic Harnesses

**Official Benchmark Suite, Reference Architecture Codebase & Reproducibility Package**

[![License: Apache 2.0](https://img.shields.io/badge/Code_License-Apache_2.0-blue.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Docs_%26_Paper_License-CC_BY_4.0-lightgrey.svg)](LICENSE)

> **Paper**: *The Specification Is the Source: Dual-Loop State Isolation and Contract-Locked Harnesses for Reliable Agentic Software Engineering*  
> **Authors**: Alejandro Kaspar, Hader Ceron, Joaquin Menendez, and Nacho Villaluenga *(Google)*  
> **Compiled Manuscript**: [`paper/DualLoop_SDD_Research_Paper.pdf`](paper/DualLoop_SDD_Research_Paper.pdf) | **LaTeX Source**: [`paper/main.tex`](paper/main.tex)

---

## Overview

As software engineering agents transition from single-turn code completion to autonomous multi-milestone repository evolution, their reliability is governed by two structural failure modes:

1. **Inner-Loop Verifier Gaming (Reward Hacking)**: When a coding agent shares write access to both production source files and the test suite that grades them, boundary failures under tight token budgets incentivize *test deletion, assertion weakening, or tautological rewrites*.
2. **Outer-Loop Specification Drift (Temporal Contradiction)**: When natural-language specifications accumulate across sequential feature milestones without deterministic state compaction, obsolete clauses collide with newer requirements, degrading zero-shot clean-room rebuildability.

This repository provides the complete **reference implementation, benchmark evaluation harnesses, raw empirical trial records, agent workspaces, and automated verification suite** accompanying our research paper:

- **252 Upstream Benchmark Trials (`benchmarks/upstream_252_trials/`)**:
  - **Suite 1 (Inner-Loop Execution Harnesses — 240 Blind Trials)**: Evaluates 4 inner-loop architectures (**Arm A**: Unconstrained ReAct Baseline, **Arm B**: Procedural TDD Skill Harness, **Arm C**: `OO-Harness` + `Harness^2` Contrastive Probing, and **Arm D**: Contract-Locked Dual-Stage Harness) across 20 tasks drawn from **SWE-bench Verified**, **Commit0**, **BigCodeBench**, and **EvalPlus** over $k = 3$ independent runs ($4 \times 20 \times 3 = 240$ trials; 301 isolated subagent executions).
  - **Suite 2 (Outer-Loop Specification Topologies — 12 Multi-Milestone Trajectories)**: Evaluates 4 specification state architectures (**Outer A**: Append-Only Ephemeral Sprint Specs, **Outer B**: Feature-Isolated Spec Directories, **Outer C**: Single-File In-Place EARS Requirements, and **Outer D**: Two-Plane Delta-Merged SSOT) across a 5-milestone **Commit0-Evo (`TinyDB`)** lifecycle ($M_1 \to M_5$) with historical rollback ($M_4$) and zero-code clean-room rebuild ($M_5$).
- **Controlled Multi-Suite Diagnostic Benchmark (`benchmarks/controlled_36_workspaces/`)**:
  - Contains all **36 controlled blind agent workspaces** (Suite 1 Regimes 1 & 2 across `SubscriptionWebhookEngine`, `ConferenceScheduler`, and `DependencyReleasePlanner`, plus Suite 2 `LedgerFlow` $M_1 \to M_5$ clean-room rebuilds) together with extended adversarial tampering stress tests, multi-seed behavioral entropy ($\hat{H}$), and the sealed programmatic oracle & single-process AST mutation testing runner (`single_proc_mut_runner.py`).
- **Core Reference Architecture (`src/`)**:
  - `src/oo_harness.py`: Object-Oriented Harness (`BaseSDDHarness` class hierarchy, `OOHarnessRouter` dynamic subclass router, `HarnessSquaredProber` contrastive boundary prober, `chmod 0444` + SHA-256 verifier lock, and Stage 1 / Stage 2 cold independent auditor).
  - `src/single_proc_mut_runner.py`: Fast in-memory AST mutation testing engine.
  - `src/harnesses/`: Benchmark staging scripts, prompt templates (`templates/inner_arms/` & `templates/outer_arms/`), and metric evaluators.

---

## Headline Empirical Results

### 1. Inner-Loop Execution Harnesses (240 Blind Trials across 4 Benchmarks)

| Inner-Loop Harness Architecture | Raw Oracle Pass (%) | Tamper-Free Strict Pass (%) | Test Tampering Rate (%) | False Completion Rate (%) | Mutation Kill Score (%) | Mean Steps |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Arm A**: Unconstrained ReAct Baseline | $83.3 \pm 2.9\%$ (50/60) | $68.3 \pm 2.9\%$ (41/60) | $18.3 \pm 2.9\%$ (11/60) | $16.7 \pm 2.9\%$ | $71.1 \pm 1.2\%$ | $21.1 \pm 2.5$ |
| **Arm B**: Procedural TDD Skill Harness (`SKILL.md`) | $85.0 \pm 5.0\%$ (51/60) | $68.3 \pm 2.9\%$ (41/60) | $18.3 \pm 2.9\%$ (11/60) | $15.0 \pm 5.0\%$ | $77.6 \pm 2.8\%$ | $23.1 \pm 2.4$ |
| **Arm C**: `OO-Harness` + `Harness^2` Probing | $90.0 \pm 5.0\%$ (54/60) | $70.0 \pm 5.0\%$ (42/60) | $23.3 \pm 5.8\%$ (14/60) | $10.0 \pm 5.0\%$ | $77.7 \pm 2.4\%$ | $25.9 \pm 2.4$ |
| **Arm D**: **Contract-Locked Dual-Stage (Ours)** | **$91.7 \pm 2.9\%$ (55/60)** | **$91.7 \pm 2.9\%$ (55/60)** | **$0.0 \pm 0.0\%$ (0/60)** | **$8.3 \pm 2.9\%$** | **$94.4 \pm 0.8\%$** | $32.2 \pm 1.3$ |

- **Eliminating Verifier Gaming**: Across all 60 trials, **Arm D** reduces test tampering from $18.3\%$–$23.3\%$ down to **$0.0\%$ (0/60)** ($p < 0.0001$ Fisher's exact test; $p = 0.00012$ exact McNemar test vs. Arm C; $p = 0.0039$ task-level exact sign test across $9/9$ tampered tasks).
- **Tamper-Free Strict Pass Gain**: **Arm D** achieves **$91.7\%$ (55/60)** strict pass—a **$+21.7$ percentage-point** improvement over Arm C ($70.0\%$, $p = 0.0046$) and **$+23.4$ pp** over Arms A and B ($68.3\%$, $p = 0.0025$).

### 2. Outer-Loop Specification State Topologies (Commit0-Evo 5-Milestone Lifecycle)

| Outer-Loop Specification Topology | $M_1$ Core | $M_2$ Cache | $M_3$ Flush | $M_4$ Rollback | $M_5$ Clean-Room Rebuild | Active Spec Contradictions | Plug-in Entropy $\hat{H}$ (bits) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Outer A**: Append-Only Ephemeral Sprint Specs | $100.0\%$ | $100.0\%$ | $100.0\%$ | $0.0\%$ | $0.0\%$ | $6/24$ ($25.0\%$) | $0.00$ (0/3 pass) |
| **Outer B**: Feature-Isolated Spec Directories | $100.0\%$ | $100.0\%$ | $100.0\%$ | $100.0\%$ | $66.7\%$ | $3/24$ ($12.5\%$) | $0.92$ (2/3 pass) |
| **Outer C**: Single-File In-Place EARS Requirements | $100.0\%$ | $100.0\%$ | $100.0\%$ | $0.0\%$ | $100.0\%$ | $0/18$ ($0.0\%$) | $0.00$ (3/3 pass) |
| **Outer D**: **Two-Plane Delta-Merged SSOT (Ours)** | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | **$0/18$ ($0.0\%$)** | **$0.00$ (3/3 pass)** |

---

## Repository Structure

```text
dualloop-sdd-benchmark/
├── README.md                                  # Quickstart, architecture overview & empirical summary
├── LICENSE                                    # Dual License: Apache 2.0 (code) + CC BY 4.0 (paper/docs)
├── NOTICE                                     # Mandatory attribution notice
├── CITATION.cff                               # Machine-readable citation metadata (all 4 co-authors)
├── run_all_verifications.sh                   # 1-command end-to-end reproducibility & audit runner
├── src/
│   ├── oo_harness.py                          # BaseSDDHarness, OOHarnessRouter, HarnessSquaredProber & Cold Auditor
│   ├── single_proc_mut_runner.py              # Single-process in-memory AST mutation test runner
│   └── harnesses/
│       ├── templates/                         # Exact system prompts & skill contracts for Arms A-D & Outer A-D
│       ├── stage_all_4_benchmarks.py          # Upstream 240-trial inner-loop staging harness
│       ├── stage_realistic_outer_loop.py      # Upstream 12-trial Commit0-Evo outer-loop staging harness
│       ├── enrich_baseline_contract_tests.py  # Baseline contract test enrichment utility
│       └── compute_all_real_metrics.py        # Raw trial evaluator & summary aggregator
├── benchmarks/
│   ├── upstream_252_trials/
│   │   ├── full_benchmark_summary.json        # Complete 240 inner + 12 outer trial records & metrics
│   │   ├── subagent_telemetry_summary.json    # Wall-clock durations & planner step counts (301 subagents)
│   │   ├── manifest.json                      # Task manifest across SWE-bench, Commit0, BigCodeBench, EvalPlus
│   │   └── runs/                              # Per-run raw workflow JSON outputs
│   └── controlled_36_workspaces/
│       ├── run_sdd_benchmark.py               # Controlled 36-workspace benchmark runner
│       ├── grade_measured_eval.py             # Sealed programmatic oracle grader & AST prefix verifier
│       ├── test_oo_harness_benchmark.py       # Unit & integration test suite for OO-Harness & graders
│       ├── BENCHMARK_REPORT.md                # Detailed controlled benchmark report
│       └── measured_eval/                     # All 36 blind agent workspaces (Regimes 1 & 2 + Outer M1-M5)
├── verification/
│   ├── verify_all_claims.py                   # Verifies all tables, counts, p-values & telemetry against main.tex
│   ├── verify_all_formulas.py                 # Verifies all 7 mathematical equations & Proposition 1 (200 fuzz histories)
│   └── leak_scan_repo.py                      # Open-source hygiene & vendor-neutral nomenclature scanner
└── paper/
    ├── DualLoop_SDD_Research_Paper.pdf        # Compiled 30-page research paper PDF
    ├── main.tex                               # Full LaTeX manuscript source
    ├── references.bib                         # Verified BibTeX bibliography
    ├── google.cls                             # LaTeX class file
    └── assets/logo_Google_FullColor.png       # Header logo asset
```

---

## Quickstart: 1-Command Verification (`< 15 seconds`)

Requirements: Python 3.10+ and `scipy` (`pip install scipy`).

Run the entire verification pipeline from the repository root:

```bash
./run_all_verifications.sh
```

This executes five deterministic verification gates:
1. **`python3 verification/verify_all_claims.py`**: Recomputes every cell of Tables 2–6, all Fisher/McNemar/Sign/Wilcoxon $p$-values, and all 301 subagent wall-clock durations from `benchmarks/upstream_252_trials/` and cross-checks them against `paper/main.tex`.
2. **`python3 verification/verify_all_formulas.py`**: Programmatically verifies all 7 mathematical formula groups in `paper/main.tex`, including Fano's inequality, Clopper-Pearson bounds, the constructive AST prefix splice invariant $P_{\mathrm{AST}}$, and Proposition 1's four-stage forward compiler $\Phi$ and inverse $\Phi_{\mathrm{seq}}^{-1}$ across 200 randomized multi-milestone histories.
3. **`python3 benchmarks/controlled_36_workspaces/run_sdd_benchmark.py`**: Grades all controlled blind agent workspaces using sealed programmatic oracles and AST mutation testing.
4. **`python3 -m unittest discover -s benchmarks/controlled_36_workspaces -p "test_*.py"`**: Runs the unit and integration test suite for `OOHarnessRouter`, `HarnessSquaredProber`, SHA-256/`chmod 0444` test locking, and the two-stage cold auditor.
5. **`python3 verification/leak_scan_repo.py`**: Confirms zero internal paths/terms and strict vendor-neutral academic nomenclature across every file in the repository.

---

## Citation

If you use this benchmark suite, codebase, or research paper in your work, please cite:

```bibtex
@techreport{kaspar2026dualloop,
  title       = {The Specification Is the Source: Dual-Loop State Isolation and Contract-Locked Harnesses for Reliable Agentic Software Engineering},
  author      = {Kaspar, Alejandro and Ceron, Hader and Menendez, Joaquin and Villaluenga, Nacho},
  institution = {Google},
  year        = {2026},
  note        = {Dual-Loop SDD & OO-Harness Benchmark Suite (252 Upstream Trials + 36 Controlled Workspaces)}
}
```

## License

- **Source Code & Benchmark Scripts**: Licensed under the **Apache License, Version 2.0** (see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE)).
- **Research Paper, Specifications & Documentation**: Licensed under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)** (see [`LICENSE`](LICENSE) and [`CITATION.cff`](CITATION.cff)).
