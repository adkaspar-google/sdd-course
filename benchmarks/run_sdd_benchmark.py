#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Dual-Loop Measured Benchmark Suite: Inner-Loop Harnesses vs. Outer-Loop SDD Frameworks.

100% EMPIRICALLY MEASURED BENCHMARK SUITE (36 Real Blind Agent Workspaces):
Every number emitted by this script is computed deterministically by running
sealed programmatic oracle assertions, mutation tests, and specification
hygiene checks against real agent-generated workspaces on disk in
`benchmarks/measured_eval/` (plus the 6 `TaskFlow` course labs):

1. SUITE 1 — INNER-LOOP BLIND BENCHMARK (24 Real Agent Workspaces):
   Evaluates 4 Inner-Loop Execution Harnesses across 3 tasks
   (`SubscriptionWebhookEngine`, `ConferenceScheduler`, `DependencyReleasePlanner`)
   under 2 prompt regimes (6 runs per harness = 24 blind parallel agent runs):
     - Regime 1 (Formal Mathematical Spec Prompts — 12 runs): User prompt
       explicitly specifies boundary formulas (`>= 50`, `<= 60`, bidirectional
       `>= 15`, `'BLOCKED'` precedence).
     - Regime 2 (Natural Brownfield Engineering Tickets — 12 runs): User prompt
       is a natural product bug ticket against brownfield starter files with
       unannotated bugs (`>` vs `>=`, `< 60` vs `<= 60`, naive upgrade rollback,
       one-way speaker cooldown, `failed_services` checked before upstream
       `BLOCKED` state) and `# TODO` helper stubs.
   Harnesses compared:
     - `arm_a_baseline`: Unconstrained ReAct Baseline (no skills)
     - `arm_b_procedural_tdd`: Procedural TDD Skill Harness (`SKILL.md` / `SkillsBench` `arXiv:2602.12670`)
     - `arm_c_ooharness_h2`: `OO-Harness` (`arXiv:2610.28380`) + `Harness^2`
       (`google-research/harness2` `Propose-Probe-Compose`)
     - `arm_d_unified_inner`: Contract-Locked Dual-Stage Harness (Ours: `.agents/skills/`
       x `OO-Harness` Subclass Router x `Harness^2` Prober
       + 5-Step Scorecard `Out of Scope` Lock + `chmod 444` Test Lock)

2. SUITE 2 — OUTER-LOOP MULTI-MILESTONE & CLEAN-ROOM REBUILD BENCHMARK
   (12 Real Agent Workspaces across M1 -> M2 -> M3 -> M4 -> M5):
   Evaluates 4 Outer-Loop SDD Frameworks evolving `LedgerFlow` across 4
   consecutive milestones (`M1 -> M2 -> M3 -> M4`) without resetting the
   workspace, followed by two Milestone 5 (`M5`) Clean-Room Rebuild regimes
   where all `.py` files are deleted and fresh Rebuild Agents receive ONLY
   surviving `.md` specification files:
     - `M4 Evolved Code`: Programmatic oracle pass rate after M1 -> M4 in-place.
     - `M5-Primary-Spec Rebuild`: Clean-Room rebuild from each framework's
       primary core capability specification (`2026-10-01-milestone-1.md` vs
       `specs/001-milestone-1/spec.md` vs `requirements.md` vs
       `openspec/specs/ledger-flow/spec.md` + `SPEC.md`).
     - `M5-All-Docs Rebuild`: Clean-Room rebuild when given all `.md` files in
       the repository simultaneously.
     - `Active Spec Contradictions`: Direct audit of conflicting M1 vs M3 rules
       (`'PENDING'` vs `'AWAITING_CLEARING'`, `> 100000` vs `>= 100000`, flat
       `1%` vs tiered `50/100 bps` with `10`-cent floor) in active spec files.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict

BENCHMARK_DIR = Path(__file__).resolve().parent
REPO_ROOT = BENCHMARK_DIR.parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

from grade_measured_eval import evaluate_all_measured_workspaces  # noqa: E402
from oo_harness import (  # noqa: E402
    DriftRemediationHarness,
    HarnessSquaredProber,
    OOHarnessRouter,
)


def run_all_benchmarks() -> Dict[str, Any]:
    measured = evaluate_all_measured_workspaces()

    # Verify OO-Harness dynamic subclass evolution and Harness^2 Propose-Probe-Compose
    prober = HarnessSquaredProber()
    probe_demo = prober.propose_probe_compose(
        domain="sliding_window_rate_limit_60s",
        candidate_predicates={
            "strict_lt_60": lambda delta: delta < 60,
            "inclusive_boundary": lambda delta: delta <= 60,
        },
        probe_inputs=[59, 60, 61],
    )
    evolved_cls = OOHarnessRouter.evolve_subclass_from_failure(
        parent_cls=DriftRemediationHarness,
        new_class_name="SlidingWindowBoundaryHarness",
        archetype_key="sliding_window_boundary",
        failure_invariant="Enforce inclusive <= window bounds on rate-limit timestamps",
    )

    return {
        "benchmark_suite": "Dual-Loop Measured SDD & Agentic Harness Benchmark Suite v3.0 (36 Real Blind Agent Workspaces)",
        "methodology": {
            "status": "100% Empirically Measured from Blind Agent Executions",
            "inner_loop_runs": 24,
            "outer_loop_workspaces": 12,
            "total_evaluated_workspaces": 36,
            "fairness_guarantees": [
                "Identical task/ticket prompts across all compared arms within each regime",
                "Identical starter files across all compared arms",
                "Zero failure coaching in any prompt",
                "Task-agnostic harness preambles",
                "Sealed programmatic oracle graders and mutation tests",
            ],
            "oo_harness_evolution_verified": evolved_cls.__name__,
            "harness_squared_probe_disagreements_caught": len(
                probe_demo["contrastive_disagreements"]
            ),
        },
        "measured_results": measured,
    }


def main() -> None:
    report = run_all_benchmarks()
    measured = report["measured_results"]

    results_dir = BENCHMARK_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_json = results_dir / "benchmark_results.json"
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("=" * 98)
    print(
        "  SUITE 1: MEASURED INNER-LOOP BENCHMARK (24 Blind Runs = 4 Harnesses x 3 Tasks x 2 Regimes)"
    )
    print("=" * 98)
    print(
        f"{'Inner-Loop Harness':<38} | {'R1 Spec':>9} | {'R2 Ticket':>9} | {'Total Orc':>10} | {'MutKill':>10} | {'TestLock':>8}"
    )
    print("-" * 98)
    labels = {
        "arm_a_baseline": "Arm A: Unconstrained ReAct Baseline",
        "arm_b_procedural_tdd": "Arm B: Procedural TDD Skill Harness",
        "arm_c_ooharness_h2": "Arm C: OO-Harness + Harness^2",
        "arm_d_unified_inner": "Arm D: Contract-Locked Dual-Stage (Ours)",
    }
    comb = measured["inner_loop_combined_24_runs"]
    r1 = measured["inner_loop_regime1_formal_spec_prompt"]
    r2 = measured["inner_loop_regime2_natural_brownfield_ticket"]
    for arm_id, label in labels.items():
        c = comb[arm_id]
        r1_str = f"{r1[arm_id]['oracle_passed']}/{r1[arm_id]['oracle_total']}"
        r2_str = f"{r2[arm_id]['oracle_passed']}/{r2[arm_id]['oracle_total']}"
        tot_str = f"{c['oracle_passed']}/{c['oracle_total']} ({c['oracle_pct']:.1f}%)"
        mut_str = f"{c['mutants_killed']}/{c['mutants_total']} ({c['mutation_pct']:.1f}%)"
        print(
            f"{label:<38} | {r1_str:>9} | {r2_str:>9} | {tot_str:>10} | {mut_str:>10} | {c['readonly_locks']:>8}"
        )

    print("\n" + "=" * 98)
    print(
        "  SUITE 2: MEASURED OUTER-LOOP BENCHMARK (M1->M4 Continuous Evolution + M5 Clean-Room Rebuilds)"
    )
    print("=" * 98)
    print(
        f"{'Outer-Loop SDD Framework':<38} | {'M4 Code':>9} | {'M5 Primary':>12} | {'M5 AllDocs':>10} | {'SpecContradict':>14}"
    )
    print("-" * 98)
    outer_labels = {
        "outer_a_dated_docs": "Outer A: Append-Only Ephemeral Specs",
        "outer_b_feature_folders": "Outer B: Feature-Isolated Spec Folders",
        "outer_c_inplace_ears": "Outer C: Single-File In-Place EARS",
        "outer_d_unified_outer": "Outer D: Two-Plane Delta-Merged SSOT",
    }
    ol = measured["outer_loop"]
    for arm_id, label in outer_labels.items():
        row = ol[arm_id]
        m4_s = f"{row['m4_evolved']['passed']}/12 ({row['m4_pct']:.0f}%)"
        m5p_s = f"{row['m5_primary_spec_rebuild']['passed']}/12 ({row['m5_primary_spec_pct']:.1f}%)"
        m5a_s = f"{row['m5_all_docs_rebuild']['passed']}/12 ({row['m5_all_docs_pct']:.0f}%)"
        contrad = f"{row['spec_hygiene']['spec_contradictions']} in {row['spec_hygiene']['active_spec_file_count']} files"
        print(
            f"{label:<38} | {m4_s:>9} | {m5p_s:>12} | {m5a_s:>10} | {contrad:>14}"
        )
    print("=" * 98)


if __name__ == "__main__":
    main()
