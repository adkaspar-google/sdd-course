"""Unit tests for DependencyReleasePlanner."""

import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):
    def test_register_service_version_validation(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("auth", "0.0.0")
        planner.register_service("api", "1.2.10", depends_on=["auth"], critical=True)
        self.assertEqual(planner.services["auth"]["version"], "0.0.0")
        self.assertEqual(planner.services["api"]["version"], "1.2.10")

        invalid_versions = [
            "",
            "1.2",
            "1.2.3.4",
            "1.2.a",
            "a.b.c",
            "-1.0.0",
            "1.-2.3",
            "+1.2.3",
            "1..2",
            " 1.2.3",
            "1.2.3 ",
            "1.2.3-beta",
        ]
        for bad_ver in invalid_versions:
            with self.subTest(version=bad_ver):
                with self.assertRaises(ValueError):
                    planner.register_service("svc", bad_ver)

    def test_register_service_name_and_self_dependency(self) -> None:
        planner = DependencyReleasePlanner()
        with self.assertRaises(ValueError):
            planner.register_service("", "1.0.0")
        with self.assertRaises(ValueError):
            planner.register_service("   ", "1.0.0")
        with self.assertRaises(ValueError):
            planner.register_service("api", "1.0.0", depends_on=["api"])

    def test_compute_release_waves_and_cycles(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("auth", "1.0.0", depends_on=["db"])
        planner.register_service("api", "1.0.0", depends_on=["auth", "cache"])
        self.assertEqual(
            planner.compute_release_waves(),
            [["cache", "db"], ["auth"], ["api"]],
        )

        cycle_planner = DependencyReleasePlanner()
        cycle_planner.register_service("a", "1.0.0", depends_on=["b"])
        cycle_planner.register_service("b", "1.0.0", depends_on=["a"])
        with self.assertRaises(ValueError):
            cycle_planner.compute_release_waves()

    def test_simulate_rollout_blocked_overrides_failed_and_prevents_critical_halt(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: db (non-critical), cache (non-critical)
        planner.register_service("db", "1.0.0", critical=False)
        planner.register_service("cache", "1.0.0", critical=False)
        # Wave 1: auth (critical, depends on db), search (non-critical, depends on cache)
        planner.register_service("auth", "1.0.0", depends_on=["db"], critical=True)
        planner.register_service("search", "1.0.0", depends_on=["cache"], critical=False)
        # Wave 2: checkout (depends on auth), recommendations (depends on search)
        planner.register_service("checkout", "1.0.0", depends_on=["auth"])
        planner.register_service("recommendations", "1.0.0", depends_on=["search"])

        # db fails in Wave 0.
        # auth is in failed_services AND is critical, but its dependency db failed in Wave 0,
        # so auth must be BLOCKED (not FAILED) and must NOT trigger a halt!
        result = planner.simulate_rollout(failed_services=["db", "auth", "checkout"])
        self.assertEqual(result["failed"], ["db"])
        self.assertEqual(result["blocked"], ["auth", "checkout"])
        self.assertEqual(result["deployed"], ["cache", "recommendations", "search"])
        self.assertFalse(result["halt_triggered"])

    def test_simulate_rollout_critical_failure_halts_subsequent_waves_only(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: auth (critical), metrics (non-critical)
        planner.register_service("auth", "1.0.0", critical=True)
        planner.register_service("metrics", "1.0.0", critical=False)
        # Wave 1: dashboard (depends on metrics)
        planner.register_service("dashboard", "1.0.0", depends_on=["metrics"])

        # auth fails in Wave 0; metrics is in the same wave so it still deploys.
        # Wave 1 (dashboard) is blocked because critical service auth failed in Wave 0,
        # even if dashboard is also in failed_services.
        result = planner.simulate_rollout(failed_services=["auth", "dashboard"])
        self.assertTrue(result["halt_triggered"])
        self.assertEqual(result["deployed"], ["metrics"])
        self.assertEqual(result["failed"], ["auth"])
        self.assertEqual(result["blocked"], ["dashboard"])

    def test_impact_radius_transitive_and_wave_ordered(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: core, extra
        planner.register_service("core", "1.0.0")
        planner.register_service("extra", "1.0.0")
        # Wave 1: z_svc (depends on core), m_svc (depends on core), other (depends on extra)
        planner.register_service("z_svc", "1.0.0", depends_on=["core"])
        planner.register_service("m_svc", "1.0.0", depends_on=["core"])
        planner.register_service("other", "1.0.0", depends_on=["extra"])
        # Wave 2: a_svc (depends on z_svc), b_svc (depends on other)
        planner.register_service("a_svc", "1.0.0", depends_on=["z_svc"])
        planner.register_service("b_svc", "1.0.0", depends_on=["other"])
        # Wave 3: final_svc (depends on a_svc and b_svc)
        planner.register_service("final_svc", "1.0.0", depends_on=["a_svc", "b_svc"])

        # Transitive downstream of "core":
        # Wave 1: m_svc, z_svc
        # Wave 2: a_svc
        # Wave 3: final_svc
        # Notice a_svc is alphabetically before m_svc/z_svc, but in Wave 2 so it comes after Wave 1.
        self.assertEqual(
            planner.impact_radius("core"),
            ["m_svc", "z_svc", "a_svc", "final_svc"],
        )
        self.assertEqual(planner.impact_radius("final_svc"), [])

        with self.assertRaises(ValueError):
            planner.impact_radius("nonexistent")


if __name__ == "__main__":
    unittest.main()
