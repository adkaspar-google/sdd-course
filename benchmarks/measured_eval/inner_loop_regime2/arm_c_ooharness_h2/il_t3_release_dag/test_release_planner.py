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
"""Unit tests for DependencyReleasePlanner."""

import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):
    def test_register_service_version_validation(self) -> None:
        planner = DependencyReleasePlanner()
        # Inclusive boundary: 0.0.0 is valid (three non-negative integers >= 0)
        planner.register_service("auth", "0.0.0")
        planner.register_service("api", "1.12.300", depends_on=["auth"])
        self.assertEqual(planner.services["auth"]["version"], "0.0.0")
        self.assertEqual(planner.services["api"]["version"], "1.12.300")

        invalid_versions = [
            "",
            "1.0",
            "1.0.0.0",
            "-1.0.0",
            "1.-2.0",
            "1.0.-3",
            "+1.0.0",
            "1.2.a",
            "a.b.c",
            "1..2",
            ".1.2",
            "1.2.",
            " 1.2.3",
            "1.2.3 ",
            "1. 2.3",
            "1.2.3-alpha",
            "v1.2.3",
        ]
        for bad_ver in invalid_versions:
            with self.subTest(version=bad_ver):
                with self.assertRaises(ValueError):
                    planner.register_service("svc", bad_ver)

        # Ensure failed in-place update does not corrupt existing service
        with self.assertRaises(ValueError):
            planner.register_service("auth", "1.bad.0")
        self.assertEqual(planner.services["auth"]["version"], "0.0.0")

    def test_register_service_name_and_self_dependency(self) -> None:
        planner = DependencyReleasePlanner()
        with self.assertRaises(ValueError):
            planner.register_service("", "1.0.0")
        with self.assertRaises(ValueError):
            planner.register_service("   ", "1.0.0")
        with self.assertRaises(ValueError):
            planner.register_service("auth", "1.0.0", depends_on=["auth"])
        with self.assertRaises(ValueError):
            planner.register_service(" auth ", "1.0.0", depends_on=["auth"])

    def test_compute_release_waves_and_cycles(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertEqual(planner.compute_release_waves(), [])

        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("auth", "1.0.0", depends_on=["db", "cache"])
        planner.register_service("gateway", "1.0.0", depends_on=["auth"])

        waves = planner.compute_release_waves()
        self.assertEqual(waves, [["cache", "db"], ["auth"], ["gateway"]])

        # Unknown dependency error
        bad_planner = DependencyReleasePlanner()
        bad_planner.register_service("api", "1.0.0", depends_on=["missing"])
        with self.assertRaises(ValueError):
            bad_planner.compute_release_waves()

        # Cycle detection
        cycle_planner = DependencyReleasePlanner()
        cycle_planner.register_service("a", "1.0.0", depends_on=["b"])
        cycle_planner.register_service("b", "1.0.0", depends_on=["a"])
        with self.assertRaises(ValueError):
            cycle_planner.compute_release_waves()

    def test_simulate_rollout_blocked_precedence_and_blocked_critical_no_halt(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: db, metrics
        planner.register_service("db", "1.0.0", critical=False)
        planner.register_service("metrics", "1.0.0", critical=False)
        # Wave 1: auth (critical, depends on db), exporter (depends on metrics)
        planner.register_service("auth", "1.0.0", depends_on=["db"], critical=True)
        planner.register_service("exporter", "1.0.0", depends_on=["metrics"], critical=False)
        # Wave 2: billing (depends on auth), dashboard (depends on exporter)
        planner.register_service("billing", "1.0.0", depends_on=["auth"], critical=False)
        planner.register_service("dashboard", "1.0.0", depends_on=["exporter"], critical=False)

        # db fails in Wave 0; auth is also listed in failed_services and is critical.
        # Because db failed in Wave 0, auth is prevented from running in Wave 1 and MUST
        # be marked BLOCKED (not FAILED), and MUST NOT trigger a critical halt!
        # Thus exporter and dashboard must deploy cleanly.
        result = planner.simulate_rollout(failed_services=["db", "auth", "billing"])
        self.assertEqual(result["failed"], ["db"])
        self.assertEqual(result["blocked"], ["auth", "billing"])
        self.assertEqual(result["deployed"], ["dashboard", "exporter", "metrics"])
        self.assertFalse(result["halt_triggered"])

    def test_simulate_rollout_critical_failure_halts_later_waves(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: auth (critical), metrics (non-critical)
        planner.register_service("auth", "1.0.0", critical=True)
        planner.register_service("metrics", "1.0.0", critical=False)
        # Wave 1: api (depends on auth), exporter (depends on metrics)
        planner.register_service("api", "1.0.0", depends_on=["auth"])
        planner.register_service("exporter", "1.0.0", depends_on=["metrics"])

        # auth fails in Wave 0 -> metrics still deploys in Wave 0,
        # but Wave 1 (both api and exporter) is blocked, even if exporter is in failed_services.
        result = planner.simulate_rollout(failed_services=["auth", "exporter"])
        self.assertEqual(result["failed"], ["auth"])
        self.assertEqual(result["deployed"], ["metrics"])
        self.assertEqual(result["blocked"], ["api", "exporter"])
        self.assertTrue(result["halt_triggered"])

    def test_impact_radius_transitive_ordered_by_wave_then_alpha(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: root, other_root
        planner.register_service("root", "1.0.0")
        planner.register_service("other_root", "1.0.0")
        # Wave 1: z_mid (depends on root), b_mid (depends on root), unrelated (depends on other_root)
        planner.register_service("z_mid", "1.0.0", depends_on=["root"])
        planner.register_service("b_mid", "1.0.0", depends_on=["root"])
        planner.register_service("unrelated", "1.0.0", depends_on=["other_root"])
        # Wave 2: a_leaf (depends on z_mid), c_leaf (depends on b_mid)
        planner.register_service("a_leaf", "1.0.0", depends_on=["z_mid"])
        planner.register_service("c_leaf", "1.0.0", depends_on=["b_mid"])
        # Wave 3: final (depends on a_leaf and c_leaf)
        planner.register_service("final", "1.0.0", depends_on=["a_leaf", "c_leaf"])

        # Note that alphabetically "a_leaf" < "b_mid" < "c_leaf" < "final" < "z_mid",
        # but wave ordering requires Wave 1 ["b_mid", "z_mid"], then Wave 2 ["a_leaf", "c_leaf"], then Wave 3 ["final"].
        self.assertEqual(
            planner.impact_radius("root"),
            ["b_mid", "z_mid", "a_leaf", "c_leaf", "final"],
        )
        self.assertEqual(planner.impact_radius("z_mid"), ["a_leaf", "final"])
        self.assertEqual(planner.impact_radius("final"), [])

        with self.assertRaises(ValueError):
            planner.impact_radius("nonexistent")


if __name__ == "__main__":
    unittest.main()
