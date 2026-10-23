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
    def test_register_service_valid_versions(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("auth", "1.0.0", critical=True)
        planner.register_service("api", "0.12.345", depends_on=["auth", "auth"])
        self.assertEqual(planner.services["auth"]["version"], "1.0.0")
        self.assertEqual(planner.services["api"]["depends_on"], ["auth"])

    def test_register_service_invalid_versions_rejected(self) -> None:
        planner = DependencyReleasePlanner()
        invalid_versions = [
            "1.0",
            "1.0.0.0",
            "1.a.0",
            "-1.0.0",
            "1.-2.0",
            "1.0.-3",
            "+1.0.0",
            "1..0",
            "1.0.",
            ".1.0",
            " 1.0.0",
            "1.0.0 ",
            "1. 0.0",
            "",
        ]
        for bad_ver in invalid_versions:
            with self.subTest(version=bad_ver):
                with self.assertRaises(ValueError):
                    planner.register_service("svc", bad_ver)

    def test_register_service_invalid_name_and_self_dependency(self) -> None:
        planner = DependencyReleasePlanner()
        with self.assertRaises(ValueError):
            planner.register_service("", "1.0.0")
        with self.assertRaises(ValueError):
            planner.register_service("   ", "1.0.0")
        with self.assertRaises(ValueError):
            planner.register_service("auth", "1.0.0", depends_on=["auth"])

    def test_compute_release_waves_and_errors(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertEqual(planner.compute_release_waves(), [])

        planner.register_service("db", "1.0.0", critical=True)
        planner.register_service("cache", "1.0.0")
        planner.register_service("api", "1.0.0", depends_on=["db", "cache"])
        planner.register_service("web", "1.0.0", depends_on=["api"])
        self.assertEqual(
            planner.compute_release_waves(),
            [["cache", "db"], ["api"], ["web"]],
        )

    def test_compute_release_waves_unknown_dep_and_cycle(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("api", "1.0.0", depends_on=["missing"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

        cycle_planner = DependencyReleasePlanner()
        cycle_planner.register_service("a", "1.0.0", depends_on=["b"])
        cycle_planner.register_service("b", "1.0.0", depends_on=["a"])
        with self.assertRaises(ValueError):
            cycle_planner.compute_release_waves()

    def test_simulate_rollout_blocked_service_in_failed_services_is_blocked_not_failed(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0", critical=False)
        planner.register_service("api", "1.0.0", depends_on=["db"], critical=True)
        planner.register_service("independent", "1.0.0", critical=False)
        planner.register_service("independent_child", "1.0.0", depends_on=["independent"])

        # db fails in wave 0 (non-critical).
        # api (critical) is in wave 1 and depends on db, AND is also listed in failed_services.
        # Because db failed in wave 0, api must be BLOCKED (not FAILED) and must NOT trigger a halt!
        result = planner.simulate_rollout(["db", "api"])
        self.assertEqual(result["waves"], [["db", "independent"], ["api", "independent_child"]])
        self.assertEqual(result["failed"], ["db"])
        self.assertEqual(result["blocked"], ["api"])
        self.assertEqual(result["deployed"], ["independent", "independent_child"])
        self.assertFalse(result["halt_triggered"])

    def test_simulate_rollout_critical_failure_halts_subsequent_waves_only(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("alpha_crit", "1.0.0", critical=True)
        planner.register_service("zeta_peer", "1.0.0", critical=False)
        planner.register_service("next_wave_svc", "1.0.0", depends_on=["zeta_peer"])
        planner.register_service("next_wave_failing", "1.0.0", depends_on=["zeta_peer"])

        # alpha_crit and zeta_peer are both in wave 0.
        # alpha_crit fails in wave 0 -> zeta_peer in wave 0 still deploys,
        # while wave 1 services are BLOCKED (even next_wave_failing in failed_services).
        result = planner.simulate_rollout(["alpha_crit", "next_wave_failing"])
        self.assertEqual(
            result["waves"],
            [["alpha_crit", "zeta_peer"], ["next_wave_failing", "next_wave_svc"]],
        )
        self.assertEqual(result["failed"], ["alpha_crit"])
        self.assertEqual(result["deployed"], ["zeta_peer"])
        self.assertEqual(result["blocked"], ["next_wave_failing", "next_wave_svc"])
        self.assertTrue(result["halt_triggered"])

    def test_impact_radius_transitive_and_wave_ordered(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: core, other
        planner.register_service("core", "1.0.0")
        planner.register_service("other", "1.0.0")
        # Wave 1: z_mid (depends on core), a_other_mid (depends on other)
        planner.register_service("z_mid", "1.0.0", depends_on=["core"])
        planner.register_service("a_other_mid", "1.0.0", depends_on=["other"])
        # Wave 2: b_leaf (depends on z_mid), a_leaf (depends on z_mid), m_bridge (depends on core and a_other_mid)
        planner.register_service("b_leaf", "1.0.0", depends_on=["z_mid"])
        planner.register_service("a_leaf", "1.0.0", depends_on=["z_mid"])
        planner.register_service("m_bridge", "1.0.0", depends_on=["core", "a_other_mid"])
        # Wave 3: a_deep (depends on b_leaf)
        planner.register_service("a_deep", "1.0.0", depends_on=["b_leaf"])

        # Transitive downstream of "core":
        # Wave 1: z_mid
        # Wave 2: a_leaf, b_leaf, m_bridge
        # Wave 3: a_deep
        self.assertEqual(
            planner.impact_radius("core"),
            ["z_mid", "a_leaf", "b_leaf", "m_bridge", "a_deep"],
        )
        self.assertEqual(planner.impact_radius("a_deep"), [])

        with self.assertRaises(ValueError):
            planner.impact_radius("nonexistent")


if __name__ == "__main__":
    unittest.main()
