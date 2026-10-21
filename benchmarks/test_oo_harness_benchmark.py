#!/usr/bin/env python3
# Copyright 2026 Alejandro Kaspar - AI Forward Deployed Engineer
# Licensed under the Apache License, Version 2.0 (the "License") and CC BY 4.0.
"""Unit & integration test suite for the Dual-Loop Open SDD & OO-Harness Benchmark Suite."""

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
from run_sdd_benchmark import (  # noqa: E402
    evaluate_inner_loop_harnesses,
    evaluate_outer_loop_sdd_frameworks,
    run_all_benchmarks,
)


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

    def test_inner_loop_and_outer_loop_suites(self) -> None:
        inner = evaluate_inner_loop_harnesses()
        outer = evaluate_outer_loop_sdd_frameworks()
        self.assertEqual(len(inner), 6)
        self.assertEqual(len(outer), 5)

        # Verify our Unified Inner Loop (Inner-6) beats Vanilla Superpowers (Inner-3),
        # Standalone OO-Harness (Inner-4), and Standalone Harness^2 (Inner-5)
        by_id = {r["inner_id"]: r for r in inner}
        self.assertLess(
            by_id["inner_3_vanilla_superpowers"]["single_task_pass_at_1_pct"],
            by_id["inner_6_unified_superpowers_ooharness_h2"]["single_task_pass_at_1_pct"],
        )
        self.assertLess(
            by_id["inner_4_oo_harness_standalone"]["single_task_pass_at_1_pct"],
            by_id["inner_6_unified_superpowers_ooharness_h2"]["single_task_pass_at_1_pct"],
        )
        self.assertLess(
            by_id["inner_5_harness_squared_standalone"]["single_task_pass_at_1_pct"],
            by_id["inner_6_unified_superpowers_ooharness_h2"]["single_task_pass_at_1_pct"],
        )

        # Verify our Unified Outer Loop (Outer-5) beats Ephemeral Queues (Outer-1),
        # BMAD (Outer-2), GitHub Spec Kit (Outer-3), and Kiro (Outer-4) across M1->M5
        outer_by_id = {r["framework_id"]: r for r in outer}
        for competitor in (
            "outer_1_ephemeral_task_queues",
            "outer_2_bmad_agile_personas",
            "outer_3_github_spec_kit",
            "outer_4_amazon_kiro_ears",
        ):
            self.assertLess(
                outer_by_id[competitor]["m1_to_m5_cumulative_pass_pct"],
                outer_by_id["outer_5_unified_conductor_openspec_ssot"][
                    "m1_to_m5_cumulative_pass_pct"
                ],
            )

    def test_four_arm_benchmark_monotonic_lift(self) -> None:
        report = run_all_benchmarks(live_ablation_dir=None)
        self.assertEqual(report["tasks_total"], 12)
        arms = {a["arm_id"]: a for a in report["arms"]}
        self.assertLess(
            arms["arm1"]["partial_credit_avg_pct"],
            arms["arm2"]["partial_credit_avg_pct"],
        )
        self.assertLess(
            arms["arm2"]["partial_credit_avg_pct"],
            arms["arm3"]["partial_credit_avg_pct"],
        )
        self.assertLess(
            arms["arm3"]["partial_credit_avg_pct"],
            arms["arm4"]["partial_credit_avg_pct"],
        )
        self.assertEqual(arms["arm4"]["strict_pass_at_1_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
