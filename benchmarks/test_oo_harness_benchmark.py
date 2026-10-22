#!/usr/bin/env python3
# Copyright 2026 Alejandro Kaspar - AI Forward Deployed Engineer
# Licensed under the Apache License, Version 2.0 (the "License") and CC BY 4.0.
"""Unit & integration test suite for the Dual-Loop Measured SDD & OO-Harness Benchmark Suite."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

from oo_harness import (  # noqa: E402
    BaseSDDHarness,
    BrownfieldSyncHarness,
    CleanRoomRebuildHarness,
    DriftRemediationHarness,
    GreenfieldSpecHarness,
    HarnessSquaredProber,
    MultiAppWorkflowHarness,
    OOHarnessRouter,
    TDDActuationHarness,
)
from run_sdd_benchmark import run_all_benchmarks  # noqa: E402


class TestDualLoopBenchmarkSuite(unittest.TestCase):
    """Tests both the Inner-Loop Harness Suite and Outer-Loop SDD Suite."""

    def test_inheritance_and_overridden_hooks(self) -> None:
        subclasses = [
            GreenfieldSpecHarness,
            BrownfieldSyncHarness,
            TDDActuationHarness,
            DriftRemediationHarness,
            MultiAppWorkflowHarness,
            CleanRoomRebuildHarness,
        ]
        for cls in subclasses:
            instance = cls()
            self.assertIsInstance(instance, BaseSDDHarness)
            self.assertGreaterEqual(len(instance.inherited_guardrails()), 6)
            self.assertGreaterEqual(len(instance.overridden_methods()), 1)

    def test_router_dispatches_all_six_archetypes(self) -> None:
        cases = [
            ({"prompt": "Build greenfield TodoList"}, GreenfieldSpecHarness),
            ({"has_legacy_code": True, "prompt": "Brownfield sync"}, BrownfieldSyncHarness),
            ({"prompt": "Implement streak boundary TDD"}, TDDActuationHarness),
            ({"has_failing_regression": True, "prompt": "Fix drift"}, DriftRemediationHarness),
            ({"multi_app_workflow": True, "prompt": "Webhook workflow"}, MultiAppWorkflowHarness),
            ({"clean_room_rebuild": True, "prompt": "Clean-room rebuild"}, CleanRoomRebuildHarness),
        ]
        for meta, expected_cls in cases:
            routed = OOHarnessRouter.route(meta)
            self.assertIsInstance(routed, expected_cls)

    def test_oo_harness_dynamic_subclass_evolution(self) -> None:
        evolved_cls = OOHarnessRouter.evolve_subclass_from_failure(
            parent_cls=DriftRemediationHarness,
            new_class_name="ConcurrencyLockOrderHarness",
            archetype_key="concurrency_lock_order",
            failure_invariant="Verify lock ordering DAG before async await",
        )
        self.assertTrue(issubclass(evolved_cls, DriftRemediationHarness))
        routed = OOHarnessRouter.route({"evolved_archetype": "concurrency_lock_order"})
        self.assertIsInstance(routed, evolved_cls)
        pre = routed.pre_flight({})
        self.assertIn("Verify lock ordering DAG before async await", pre["invariants"])

    def test_harness_squared_propose_probe_compose(self) -> None:
        prober = HarnessSquaredProber()
        res = prober.propose_probe_compose(
            domain="vip_threshold_cents",
            candidate_predicates={
                "strict_gt": lambda cents: cents > 100000,
                "inclusive_boundary": lambda cents: cents >= 100000,
            },
            probe_inputs=[99999, 100000, 100001],
        )
        self.assertEqual(len(res["contrastive_disagreements"]), 1)
        self.assertEqual(res["contrastive_disagreements"][0]["probe_input"], 100000)
        self.assertEqual(res["selected_candidate"], "inclusive_boundary")
        self.assertEqual(len(prober.experience_bank), 1)

    def test_verifier_file_lock_and_tamper_detection(self) -> None:
        harness = TDDActuationHarness()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_contract.py"
            test_file.write_text("assert 1 + 1 == 2\n", encoding="utf-8")
            harness.lock_verifier_files([test_file])
            self.assertTrue(harness.verify_locked_files_intact())

            harness.unlock_verifier_files()
            test_file.write_text("assert True\n", encoding="utf-8")
            self.assertFalse(harness.verify_locked_files_intact())

            audit = harness.run_two_stage_cold_audit(
                required_req_ids=["REQ-0001"],
                covered_req_ids=["REQ-0001"],
                code_quality_violations=[],
            )
            self.assertFalse(audit.stage1_passed)
            self.assertFalse(audit.approved)
            self.assertLess(audit.readiness_score, 9.0)

    def test_measured_inner_loop_and_outer_loop_results(self) -> None:
        report = run_all_benchmarks()
        self.assertEqual(report["methodology"]["total_evaluated_workspaces"], 36)
        measured = report["measured_results"]
        comb = measured["inner_loop_combined_24_runs"]

        # Verify Arm D (Contract-Locked Dual-Stage Harness) achieves 100% functional oracle (60/60),
        # beats Baseline and Procedural TDD Skill Harness on mutation kill rate, and locks 6/6 test files
        self.assertEqual(comb["arm_d_unified_inner"]["oracle_passed"], 60)
        self.assertEqual(comb["arm_d_unified_inner"]["readonly_locks"], "6/6")
        self.assertGreater(
            comb["arm_d_unified_inner"]["mutation_pct"],
            comb["arm_b_procedural_tdd"]["mutation_pct"],
        )
        self.assertGreater(
            comb["arm_d_unified_inner"]["mutation_pct"],
            comb["arm_a_baseline"]["mutation_pct"],
        )

        # Verify Outer-Loop M5-Primary-Spec Clean-Room Rebuild results:
        # Append-Only Ephemeral Specs and Feature-Isolated Folders drop to 33.3% (4/12), while Two-Plane Delta-Merged SSOT achieves 100% (12/12)
        ol = measured["outer_loop"]
        self.assertEqual(ol["outer_a_dated_docs"]["m5_primary_spec_pct"], 33.3)
        self.assertEqual(ol["outer_b_feature_folders"]["m5_primary_spec_pct"], 33.3)
        self.assertEqual(ol["outer_d_unified_outer"]["m5_primary_spec_pct"], 100.0)
        self.assertEqual(ol["outer_d_unified_outer"]["spec_hygiene"]["spec_contradictions"], 0)
        self.assertTrue(ol["outer_d_unified_outer"]["spec_hygiene"]["has_clean_room_spec_md"])
        self.assertTrue(ol["outer_d_unified_outer"]["spec_hygiene"]["has_openspec_ssot"])


if __name__ == "__main__":
    unittest.main()
