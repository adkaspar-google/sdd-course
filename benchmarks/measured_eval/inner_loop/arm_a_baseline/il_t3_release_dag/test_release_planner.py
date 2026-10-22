import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):
    def test_register_service_validation(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("auth", "1.2.0", depends_on=["db", "db", "cache"], critical=True)
        self.assertEqual(planner.services["auth"]["depends_on"], ["db", "cache"])
        self.assertTrue(planner.services["auth"]["critical"])

        for bad_name in ["", "   ", " leading", "trailing ", " both "]:
            with self.assertRaises(ValueError):
                planner.register_service(bad_name, "1.0.0")

        for bad_ver in ["1.2", "v1.0.0", "-1.0.0", "1.-2.0", "1.0.-3", "1.2.3.4", "1.2.x", "", "1.2.0-alpha"]:
            with self.assertRaises(ValueError):
                planner.register_service("svc", bad_ver)

        with self.assertRaises(ValueError):
            planner.register_service("svc", "1.0.0", depends_on=["other", "svc"])

    def test_compute_release_waves_empty_and_dag(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertEqual(planner.compute_release_waves(), [])

        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "0.1.0")
        planner.register_service("auth", "2.0.0", depends_on=["db", "cache"])
        planner.register_service("billing", "1.1.0", depends_on=["db"])
        planner.register_service("gateway", "3.0.0", depends_on=["auth", "billing"])

        waves = planner.compute_release_waves()
        self.assertEqual(waves, [["cache", "db"], ["auth", "billing"], ["gateway"]])

    def test_compute_release_waves_errors(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("a", "1.0.0", depends_on=["missing"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

        planner2 = DependencyReleasePlanner()
        planner2.register_service("a", "1.0.0", depends_on=["b"])
        planner2.register_service("b", "1.0.0", depends_on=["c"])
        planner2.register_service("c", "1.0.0", depends_on=["a"])
        with self.assertRaises(ValueError):
            planner2.compute_release_waves()

    def test_simulate_rollout_dependency_blocking(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("auth", "1.0.0", depends_on=["db"])
        planner.register_service("search", "1.0.0", depends_on=["cache"])
        planner.register_service("web", "1.0.0", depends_on=["auth", "search"])

        res = planner.simulate_rollout(failed_services=["db", "web"])
        self.assertEqual(res["waves"], [["cache", "db"], ["auth", "search"], ["web"]])
        self.assertEqual(res["deployed"], ["cache", "search"])
        self.assertEqual(res["failed"], ["db"])
        self.assertEqual(res["blocked"], ["auth", "web"])
        self.assertFalse(res["halt_triggered"])

    def test_simulate_rollout_critical_halt(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0", critical=True)
        planner.register_service("cache", "1.0.0", critical=False)
        planner.register_service("search", "1.0.0", depends_on=["cache"])
        planner.register_service("analytics", "1.0.0", depends_on=["search"], critical=True)

        # db fails in Wave 0 (critical), cache succeeds in Wave 0.
        # Wave 1 (search) and Wave 2 (analytics) must be BLOCKED even if listed in failed_services.
        res = planner.simulate_rollout(failed_services=["db", "search", "analytics"])
        self.assertEqual(res["deployed"], ["cache"])
        self.assertEqual(res["failed"], ["db"])
        self.assertEqual(res["blocked"], ["analytics", "search"])
        self.assertTrue(res["halt_triggered"])

    def test_simulate_rollout_blocked_critical_does_not_trigger_halt(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0", critical=False)
        planner.register_service("cache", "1.0.0", critical=False)
        planner.register_service("auth", "1.0.0", depends_on=["db"], critical=True)
        planner.register_service("search", "1.0.0", depends_on=["cache"], critical=False)
        planner.register_service("ui_search", "1.0.0", depends_on=["search"], critical=False)

        # db fails in Wave 0 (non-critical).
        # In Wave 1, auth is BLOCKED (due to db), so even though auth is critical and in failed_services,
        # auth did NOT fail (it was blocked), so halt_triggered is False and ui_search in Wave 2 deploys!
        res = planner.simulate_rollout(failed_services=["db", "auth"])
        self.assertEqual(res["deployed"], ["cache", "search", "ui_search"])
        self.assertEqual(res["failed"], ["db"])
        self.assertEqual(res["blocked"], ["auth"])
        self.assertFalse(res["halt_triggered"])

    def test_impact_radius(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("db", "1.0.0")
        planner.register_service("cache", "1.0.0")
        planner.register_service("users", "1.0.0", depends_on=["db"])
        planner.register_service("auth", "1.0.0", depends_on=["db", "cache"])
        planner.register_service("billing", "1.0.0", depends_on=["users"])
        planner.register_service("gateway", "1.0.0", depends_on=["auth", "billing"])

        self.assertEqual(planner.impact_radius("db"), ["auth", "users", "billing", "gateway"])
        self.assertEqual(planner.impact_radius("cache"), ["auth", "gateway"])
        self.assertEqual(planner.impact_radius("gateway"), [])

        with self.assertRaises(ValueError):
            planner.impact_radius("unknown")


if __name__ == "__main__":
    unittest.main()
