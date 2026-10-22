"""Unit tests for DependencyReleasePlanner."""

from __future__ import annotations
import unittest
from release_planner import DependencyReleasePlanner


class TestDependencyReleasePlanner(unittest.TestCase):
    def test_register_service_semver_validation(self) -> None:
        planner = DependencyReleasePlanner()
        planner.register_service("auth", "0.0.0")
        planner.register_service("billing", "1.2.3", depends_on=["auth"], critical=True)
        planner.register_service(" gateway ", "10.20.300", depends_on=["auth", "billing", "auth"])
        self.assertEqual(planner.services["gateway"]["depends_on"], ["auth", "billing"])

        invalid_versions = [
            "",
            "1.2",
            "1.2.3.4",
            "1.2.a",
            "a.b.c",
            "-1.0.0",
            "1.-2.0",
            "1.2.-3",
            "1.2.",
            ".1.2",
            "v1.2.3",
            "1.2.3-rc1",
            "1. 2.3",
            "1.2.3 ",
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
        with self.assertRaises(ValueError):
            planner.register_service(" api ", "1.0.0", depends_on=["api"])

    def test_compute_release_waves_and_errors(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertEqual(planner.compute_release_waves(), [])

        planner.register_service("api", "1.0.0", depends_on=["missing"])
        with self.assertRaises(ValueError):
            planner.compute_release_waves()

        cycle_planner = DependencyReleasePlanner()
        cycle_planner.register_service("a", "1.0.0", depends_on=["c"])
        cycle_planner.register_service("b", "1.0.0", depends_on=["a"])
        cycle_planner.register_service("c", "1.0.0", depends_on=["b"])
        with self.assertRaises(ValueError):
            cycle_planner.compute_release_waves()

    def test_simulate_rollout_blocked_before_failed_and_no_false_critical_halt(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: db_noncrit (fails), cache_ok (deploys)
        planner.register_service("db_noncrit", "1.0.0", critical=False)
        planner.register_service("cache_ok", "1.0.0", critical=False)
        # Wave 1: critical_api depends on db_noncrit, AND is in failed_services.
        # Because db_noncrit failed in Wave 0, critical_api must be BLOCKED (not FAILED)
        # and must NOT trigger a critical halt!
        planner.register_service(
            "critical_api",
            "1.0.0",
            depends_on=["db_noncrit"],
            critical=True,
        )
        planner.register_service(
            "worker_ok",
            "1.0.0",
            depends_on=["cache_ok"],
            critical=False,
        )
        # Wave 2: frontend depends on worker_ok; since critical_api was blocked (not halted),
        # frontend should still deploy!
        planner.register_service(
            "frontend",
            "1.0.0",
            depends_on=["worker_ok"],
            critical=False,
        )

        result = planner.simulate_rollout(failed_services=["db_noncrit", "critical_api"])
        self.assertEqual(
            result["waves"],
            [["cache_ok", "db_noncrit"], ["critical_api", "worker_ok"], ["frontend"]],
        )
        self.assertFalse(result["halt_triggered"])
        self.assertEqual(result["failed"], ["db_noncrit"])
        self.assertEqual(result["blocked"], ["critical_api"])
        self.assertEqual(result["deployed"], ["cache_ok", "frontend", "worker_ok"])

    def test_simulate_rollout_prior_wave_critical_halt(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: auth (critical, fails), metrics (non-critical, same wave -> deploys)
        planner.register_service("auth", "1.0.0", critical=True)
        planner.register_service("metrics", "1.0.0", critical=False)
        # Wave 1: dashboard depends only on metrics, and is also in failed_services,
        # but because critical service 'auth' failed in Wave 0, Wave 1 is blocked.
        planner.register_service("dashboard", "1.0.0", depends_on=["metrics"], critical=False)

        result = planner.simulate_rollout(failed_services=["auth", "dashboard"])
        self.assertTrue(result["halt_triggered"])
        self.assertEqual(result["deployed"], ["metrics"])
        self.assertEqual(result["failed"], ["auth"])
        self.assertEqual(result["blocked"], ["dashboard"])

    def test_impact_radius_transitive_and_wave_ordered(self) -> None:
        planner = DependencyReleasePlanner()
        # Wave 0: root, other_root
        planner.register_service("root", "1.0.0")
        planner.register_service("other_root", "1.0.0")
        # Wave 1: z_service, m_service (depend on root), unrelated (depends on other_root)
        planner.register_service("z_service", "1.0.0", depends_on=["root"])
        planner.register_service("m_service", "1.0.0", depends_on=["root"])
        planner.register_service("unrelated", "1.0.0", depends_on=["other_root"])
        # Wave 2: a_gateway (depends on z_service and m_service), b_Billing (depends on m_service)
        planner.register_service("a_gateway", "1.0.0", depends_on=["z_service", "m_service"])
        planner.register_service("b_billing", "1.0.0", depends_on=["m_service"])
        # Wave 3: aa_edge (depends on a_gateway)
        planner.register_service("aa_edge", "1.0.0", depends_on=["a_gateway"])

        # Wave 1 dependents ("m_service", "z_service") must come before Wave 2 ("a_gateway", "b_billing")
        # and Wave 3 ("aa_edge"), even though "a_gateway" and "aa_edge" are alphabetically earlier!
        self.assertEqual(
            planner.impact_radius("root"),
            ["m_service", "z_service", "a_gateway", "b_billing", "aa_edge"],
        )
        self.assertEqual(planner.impact_radius("aa_edge"), [])

        with self.assertRaises(ValueError):
            planner.impact_radius("nonexistent")

    def test_out_of_scope_todos_not_implemented(self) -> None:
        planner = DependencyReleasePlanner()
        self.assertFalse(hasattr(planner, "generate_helm_chart_yaml"))
        self.assertFalse(hasattr(planner, "notify_pagerduty_oncall"))


if __name__ == "__main__":
    unittest.main()
