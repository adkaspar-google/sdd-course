"""Comprehensive boundary and adversarial unit tests for DependencyReleasePlanner."""

import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):
    """Tests covering all equivalence classes and boundary interactions."""

    def test_register_service_valid_and_deduplication(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "0.0.1", critical=True)
        planner.register_service(
            "api", "1.2.0", depends_on=["db", "cache", "db", "auth", "cache"]
        )
        self.assertEqual(planner.services["db"]["version"], "0.0.1")
        self.assertTrue(planner.services["db"]["critical"])
        self.assertEqual(planner.services["api"]["depends_on"], ["db", "cache", "auth"])
        self.assertFalse(planner.services["api"]["critical"])

    def test_register_service_invalid_names(self) -> None:
        planner = DependencyReleasePlanner()
        for bad_name in ["", "   ", "\t\n", " leading", "trailing "]:
            with self.subTest(bad_name=bad_name):
                with self.assertRaises(ValueError):
                    planner.register_service(bad_name, "1.0.0")

    def test_register_service_invalid_versions(self) -> None:
        planner = DependencyReleasePlanner()
        bad_versions = [
            "",
            "1.2",
            "1.2.3.4",
            "v1.0.0",
            "-1.0.0",
            "1.-2.0",
            "1.2.-3",
            "1.2.a",
            "1.2.0-alpha",
            "1.2.0+build1",
            "1..0",
            ".1.0",
            " 1.0.0",
            "1.0.0 ",
            "+1.0.0",
        ]
        for bad_ver in bad_versions:
            with self.subTest(bad_ver=bad_ver):
                with self.assertRaises(ValueError):
                    planner.register_service("svc", bad_ver)

    def test_register_service_self_dependency_rejected(self) -> None:
        planner = DependencyReleasePlanner()
        with self.assertRaises(ValueError):
            planner.register_service("api", "1.0.0", depends_on=["db", "api"])

    def test_register_service_rollback_on_invalid_upgrade(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("api", "1.0.0", depends_on=["db"], critical=True)
        with self.assertRaises(ValueError):
            planner.register_service("api", "invalid_ver", depends_on=[])
        with self.assertRaises(ValueError):
            planner.register_service("api", "2.0.0", depends_on=["api"])
        # Prior record must remain intact
        self.assertEqual(planner.services["api"]["version"], "1.0.0")
        self.assertEqual(planner.services["api"]["depends_on"], ["db"])
        self.assertTrue(planner.services["api"]["critical"])

    def test_compute_release_waves_empty(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertEqual(planner.compute_release_waves(), [])

    def test_compute_release_waves_topological_and_alphabetical(self) -> None:
        planner = DependencyReleasePlanner()
        # Register out of topological and alphabetical order
        planner.register_service("frontend", "1.0.0", depends_on=["api", "cdn"])
        planner.register_service("api", "1.0.0", depends_on=["db", "auth"])
        planner.register_service("auth", "1.0.0", depends_on=["db"])
        planner.register_service("cdn", "1.0.0")
        planner.register_service("db", "1.0.0")
        planner.register_service("worker", "1.0.0", depends_on=["db"])

        waves = planner.compute_release_waves()
        self.assertEqual(
            waves,
            [
                ["cdn", "db"],          # Wave 0
                ["auth", "worker"],     # Wave 1
                ["api"],                # Wave 2 (depends on db [0] and auth [1] -> wave 2)
                ["frontend"],           # Wave 3 (depends on api [2] and cdn [0] -> wave 3)
            ],
        )

    def test_compute_release_waves_missing_dependency_raises(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("api", "1.0.0", depends_on=["missing_db"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

    def test_compute_release_waves_cycle_raises(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("root", "1.0.0")
        planner.register_service("a", "1.0.0", depends_on=["root", "c"])
        planner.register_service("b", "1.0.0", depends_on=["a"])
        planner.register_service("c", "1.0.0", depends_on=["b"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

    def test_simulate_rollout_non_critical_failure_and_blocked_override(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0", critical=False)
        planner.register_service("cache", "1.0.0", critical=False)
        planner.register_service("auth", "1.0.0", depends_on=["db"])
        planner.register_service("search", "1.0.0", depends_on=["cache"])
        planner.register_service("gateway", "1.0.0", depends_on=["auth"])

        # db fails in Wave 0.
        # auth (Wave 1) and gateway (Wave 2) depend on db, AND gateway is also in failed_services.
        # gateway and auth must be BLOCKED (not FAILED).
        # cache (Wave 0) and search (Wave 1) succeed.
        result = planner.simulate_rollout(failed_services=["db", "gateway"])
        self.assertEqual(
            result,
            {
                "waves": [
                    ["cache", "db"],
                    ["auth", "search"],
                    ["gateway"],
                ],
                "deployed": ["cache", "search"],
                "failed": ["db"],
                "blocked": ["auth", "gateway"],
                "halt_triggered": False,
            },
        )

    def test_simulate_rollout_critical_failure_halts_strictly_later_waves(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("crit_db", "1.0.0", critical=True)
        planner.register_service("peer_w0", "1.0.0", critical=False)
        planner.register_service("fail_peer_w0", "1.0.0", critical=False)
        planner.register_service("independent_w1", "1.0.0", depends_on=["peer_w0"])
        planner.register_service("also_failing_w1", "1.0.0", depends_on=["peer_w0"], critical=True)

        # crit_db fails in Wave 0 -> peer_w0 still deploys in Wave 0, fail_peer_w0 still fails in Wave 0.
        # Wave 1 is completely blocked because a critical service failed in Wave 0 (< 1),
        # even for services that only depend on peer_w0 and even if listed in failed_services!
        result = planner.simulate_rollout(
            failed_services=["crit_db", "fail_peer_w0", "also_failing_w1"]
        )
        self.assertEqual(
            result,
            {
                "waves": [
                    ["crit_db", "fail_peer_w0", "peer_w0"],
                    ["also_failing_w1", "independent_w1"],
                ],
                "deployed": ["peer_w0"],
                "failed": ["crit_db", "fail_peer_w0"],
                "blocked": ["also_failing_w1", "independent_w1"],
                "halt_triggered": True,
            },
        )

    def test_simulate_rollout_blocked_critical_service_does_not_trigger_halt(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("non_crit_w0", "1.0.0", critical=False)
        planner.register_service("healthy_w0", "1.0.0", critical=False)
        # crit_w1 is critical AND in failed_services, but its upstream non_crit_w0 fails in Wave 0!
        # So crit_w1 is BLOCKED in Wave 1 (never executes), thus halt_triggered must remain False
        # and healthy_w2 in Wave 2 must still deploy!
        planner.register_service("crit_w1", "1.0.0", depends_on=["non_crit_w0"], critical=True)
        planner.register_service("healthy_w1", "1.0.0", depends_on=["healthy_w0"])
        planner.register_service("healthy_w2", "1.0.0", depends_on=["healthy_w1"])

        result = planner.simulate_rollout(failed_services=["non_crit_w0", "crit_w1"])
        self.assertFalse(result["halt_triggered"])
        self.assertEqual(result["deployed"], ["healthy_w0", "healthy_w1", "healthy_w2"])
        self.assertEqual(result["failed"], ["non_crit_w0"])
        self.assertEqual(result["blocked"], ["crit_w1"])

    def test_impact_radius_wave_then_alphabetical_order(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("root", "1.0.0")
        planner.register_service("other_root", "1.0.0")
        planner.register_service("z_mid", "1.0.0", depends_on=["root"])
        planner.register_service("b_mid", "1.0.0", depends_on=["root"])
        planner.register_service("a_leaf", "1.0.0", depends_on=["z_mid"])
        planner.register_service("unconnected", "1.0.0", depends_on=["other_root"])

        # Wave 1 has ['b_mid', 'z_mid'], Wave 2 has ['a_leaf'].
        # Impact radius of 'root' must be ordered by wave first, then alphabetically:
        self.assertEqual(planner.impact_radius("root"), ["b_mid", "z_mid", "a_leaf"])
        self.assertEqual(planner.impact_radius("a_leaf"), [])
        self.assertEqual(planner.impact_radius("other_root"), ["unconnected"])

    def test_impact_radius_invalid_service_or_graph(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("a", "1.0.0")
        with self.assertRaises(ValueError):
            planner.impact_radius("nonexistent")

        planner.register_service("bad", "1.0.0", depends_on=["missing"])
        with self.assertRaises(ValueError):
            planner.impact_radius("a")


if __name__ == "__main__":
    unittest.main()
