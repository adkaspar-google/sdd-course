"""Unit tests for DependencyReleasePlanner."""

import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):
    def test_register_service_validation(self) -> None:
        planner = DependencyReleasePlanner()

        # Invalid names
        for bad_name in ["", "   ", " auth", "auth ", "\tauth"]:
            with self.subTest(bad_name=bad_name):
                with self.assertRaises(ValueError):
                    planner.register_service(bad_name, "1.0.0")

        # Invalid versions
        for bad_version in [
            "",
            "1.2",
            "1.2.3.4",
            "v1.0.0",
            "-1.0.0",
            "1.-2.0",
            "1.0.-3",
            "1.0.0-alpha",
            "1.a.0",
            " 1.0.0",
            "1.0.0 ",
        ]:
            with self.subTest(bad_version=bad_version):
                with self.assertRaises(ValueError):
                    planner.register_service("auth", bad_version)

        # Self-dependency
        with self.assertRaises(ValueError):
            planner.register_service("auth", "1.0.0", depends_on=["db", "auth"])

        # Valid registration and deduplication of depends_on
        planner.register_service(
            "api", "0.1.20", depends_on=["db", "cache", "db"], critical=True
        )
        self.assertEqual(planner.services["api"]["depends_on"], ["db", "cache"])
        self.assertTrue(planner.services["api"]["critical"])

    def test_compute_release_waves_empty(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertEqual(planner.compute_release_waves(), [])

    def test_compute_release_waves_topological_and_sorted(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("auth", "1.2.0", depends_on=["db", "cache"])
        planner.register_service("billing", "2.0.1", depends_on=["db"])
        planner.register_service("gateway", "3.1.0", depends_on=["auth", "billing"])
        planner.register_service("analytics", "1.0.0", depends_on=["gateway", "db"])

        waves = planner.compute_release_waves()
        self.assertEqual(
            waves,
            [
                ["cache", "db"],
                ["auth", "billing"],
                ["gateway"],
                ["analytics"],
            ],
        )

    def test_compute_release_waves_unregistered_dependency(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("auth", "1.0.0", depends_on=["missing_db"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

    def test_compute_release_waves_cycle_detection(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("a", "1.0.0", depends_on=["c"])
        planner.register_service("b", "1.0.0", depends_on=["a"])
        planner.register_service("c", "1.0.0", depends_on=["b"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

    def test_simulate_rollout_dependency_blocking(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("auth", "1.0.0", depends_on=["db"])
        planner.register_service("search", "1.0.0", depends_on=["cache"])
        planner.register_service("gateway", "1.0.0", depends_on=["auth", "search"])

        # db fails (non-critical), gateway is also in failed_services but should be BLOCKED
        result = planner.simulate_rollout(["db", "gateway"])
        self.assertEqual(
            result,
            {
                "waves": [["cache", "db"], ["auth", "search"], ["gateway"]],
                "deployed": ["cache", "search"],
                "failed": ["db"],
                "blocked": ["auth", "gateway"],
                "halt_triggered": False,
            },
        )

    def test_simulate_rollout_critical_failure_halts_subsequent_waves(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0", critical=True)
        planner.register_service("cache", "1.0.0", critical=False)
        planner.register_service("search", "1.0.0", depends_on=["cache"])
        planner.register_service("reporting", "1.0.0", depends_on=["search"], critical=True)

        # db fails in Wave 0 (critical). cache still deploys in Wave 0.
        # Wave 1 (search) and Wave 2 (reporting) are blocked even though they don't depend on db,
        # and even if search/reporting are in failed_services.
        result = planner.simulate_rollout(["db", "reporting"])
        self.assertEqual(
            result,
            {
                "waves": [["cache", "db"], ["search"], ["reporting"]],
                "deployed": ["cache"],
                "failed": ["db"],
                "blocked": ["reporting", "search"],
                "halt_triggered": True,
            },
        )

    def test_simulate_rollout_blocked_critical_service_does_not_trigger_halt(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0", critical=False)
        planner.register_service("cache", "1.0.0", critical=False)
        planner.register_service("auth", "1.0.0", depends_on=["db"], critical=True)
        planner.register_service("search", "1.0.0", depends_on=["cache"], critical=False)
        planner.register_service("ui", "1.0.0", depends_on=["search"], critical=False)

        # db fails in Wave 0 (non-critical).
        # auth (in Wave 1, critical) is in failed_services, but is BLOCKED by db failing,
        # so auth never runs and does NOT trigger halt! Thus ui in Wave 2 deploys!
        result = planner.simulate_rollout(["db", "auth"])
        self.assertEqual(
            result,
            {
                "waves": [["cache", "db"], ["auth", "search"], ["ui"]],
                "deployed": ["cache", "search", "ui"],
                "failed": ["db"],
                "blocked": ["auth"],
                "halt_triggered": False,
            },
        )

    def test_impact_radius(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("users", "1.0.0", depends_on=["db"])
        planner.register_service("auth", "1.0.0", depends_on=["db"])
        planner.register_service("search", "1.0.0", depends_on=["cache"])
        planner.register_service("gateway", "1.0.0", depends_on=["auth", "search"])
        planner.register_service("admin", "1.0.0", depends_on=["users"])

        self.assertEqual(
            planner.impact_radius("db"),
            ["auth", "users", "admin", "gateway"],
        )
        self.assertEqual(
            planner.impact_radius("cache"),
            ["search", "gateway"],
        )
        self.assertEqual(planner.impact_radius("gateway"), [])

        with self.assertRaises(ValueError):
            planner.impact_radius("unknown")


if __name__ == "__main__":
    unittest.main()
