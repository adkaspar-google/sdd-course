#!/usr/bin/env python3
# Copyright 2026 Alejandro Kaspar - AI Forward Deployed Engineer
# Licensed under the Apache License, Version 2.0 (the "License") and CC BY 4.0.
"""Unit & integration test suite for the Open SDD & OO-Harness Benchmark Suite."""

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
    BuilderStatus,
    CleanRoomRebuildHarness,
    DriftRemediationHarness,
    GreenfieldSpecHarness,
    MultiAppWorkflowHarness,
    OOHarnessRouter,
    TDDActuationHarness,
    TaskArchetype,
)
from run_sdd_benchmark import (  # noqa: E402
    BENCHMARK_TASKS,
    run_all_benchmarks,
)


class TestOOHarnessHierarchyAndRouter(unittest.TestCase):
    """Tests the Object-Oriented Harness (OO-Harness, arXiv:2610.28380) hierarchy."""

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

    def test_verifier_file_lock_and_tamper_detection(self) -> None:
        harness = TDDActuationHarness()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_contract.py"
            test_file.write_text("assert 1 + 1 == 2\n", encoding="utf-8")
            harness.lock_verifier_files([test_file])
            self.assertTrue(harness.verify_locked_files_intact())

            # Simulate reward-hacking tamper attempt
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

    def test_four_arm_benchmark_monotonic_lift(self) -> None:
        report = run_all_benchmarks(live_ablation_dir=None)
        self.assertEqual(report["tasks_total"], 12)
        arms = {a["arm_id"]: a for a in report["arms"]}

        # Verify strict progression across arms: Arm 1 < Arm 2 < Arm 3 < Arm 4
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
        self.assertEqual(arms["arm4"]["sprint_spec_sync_pct"], 100.0)
        self.assertEqual(arms["arm4"]["mutation_kill_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
