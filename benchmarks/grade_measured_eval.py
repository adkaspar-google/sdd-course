#!/usr/bin/env python3
"""Sealed Programmatic Oracle Grader for the Blind Dual-Loop Benchmark Suite.

Evaluates 36 real blind agent workspaces in `benchmarks/measured_eval/`:
  - Suite 1A (Inner-Loop Regime 1 — Formal Spec Prompts): 4 Harnesses x 3 Tasks = 12 workspaces
  - Suite 1B (Inner-Loop Regime 2 — Natural Brownfield Engineering Tickets): 4 Harnesses x 3 Tasks = 12 workspaces
  - Suite 2 (Outer-Loop Multi-Milestone Benchmark): 4 SDD Frameworks across:
      * M4 Evolved Workspace (after M1 -> M2 -> M3 -> M4)
      * M5-All-Docs Clean-Room Rebuild (rebuilt from all surviving .md files)
      * M5-Primary-Spec Clean-Room Rebuild (rebuilt from each framework's primary core capability spec)
      * Active Specification Contradiction & Hygiene Audit
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import stat
import subprocess
import sys
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent / "measured_eval"


def load_module(mod_path: pathlib.Path, unique_name: str):
    spec = importlib.util.spec_from_file_location(unique_name, str(mod_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {mod_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def check_readonly_test_lock(ws: pathlib.Path) -> bool:
    lock_manifest = ws / ".readonly_test_lock.sha256"
    for p in ws.glob("test*.py"):
        mode = p.stat().st_mode
        if not (mode & stat.S_IWUSR):
            return True
        if lock_manifest.exists():
            import hashlib
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in lock_manifest.read_text(encoding="utf-8"):
                p.chmod(0o444)
                return True
    return False


def run_agent_test_suite_against_source(ws: pathlib.Path, target_file: str, mutated_code: str) -> bool:
    """Returns True if the agent's own test suite kills (fails on) the mutant."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        for item in ws.iterdir():
            if item.is_file() and item.suffix == ".py":
                (tmp_path / item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
        (tmp_path / target_file).write_text(mutated_code, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(tmp_path), "-p", "test*.py"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.returncode != 0


# ===========================================================================
# SUITE 1: INNER-LOOP SEALED ORACLE GRADERS
# ===========================================================================


def grade_il_t1_webhook(ws: pathlib.Path, tag: str) -> dict[str, Any]:
    mod_path = ws / "webhook_engine.py"
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    try:
        mod = load_module(mod_path, f"webhook_{tag}")
        Engine = mod.SubscriptionWebhookEngine
    except Exception as exc:
        return {"error": str(exc), "checks": {}, "passed": 0, "total": 10}

    def run_check(name: str, fn):
        try:
            fn()
            checks[name] = True
        except Exception as exc:
            checks[name] = False
            errors[name] = f"{type(exc).__name__}: {exc}"

    def c1():
        eng = Engine()
        res = eng.handle_webhook({
            "webhook_id": "w1",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 10,
            "amount_cents": 25000,
            "timestamp": 100,
        })
        assert res["tier"] == "STANDARD", f"Expected STANDARD, got {res.get('tier')}"
        assert res["sla_hours"] == 24, f"Expected 24, got {res.get('sla_hours')}"
        assert len(eng.invoices) == 1

    def c2():
        eng = Engine()
        res = eng.handle_webhook({
            "webhook_id": "w_s50",
            "tenant_id": "t_s50",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "scale",
            "seats": 50,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        assert res["tier"] == "ENTERPRISE", f"seats=50 must be ENTERPRISE, got {res.get('tier')}"
        assert res["sla_hours"] == 1

    def c3():
        eng = Engine()
        res = eng.handle_webhook({
            "webhook_id": "w_a500k",
            "tenant_id": "t_a500k",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "enterprise",
            "seats": 5,
            "amount_cents": 500000,
            "timestamp": 100,
        })
        assert res["tier"] == "ENTERPRISE", f"amount_cents=500000 must be ENTERPRISE, got {res.get('tier')}"
        assert res["sla_hours"] == 1

    def c4():
        eng = Engine()
        p = {
            "webhook_id": "w_dup",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        }
        r1 = eng.handle_webhook(p)
        r2 = eng.handle_webhook(p)
        assert r1 == r2
        assert len(eng.invoices) == 1
        assert len(eng.audit_trail) == 1

    def c5():
        eng = Engine()
        try:
            eng.handle_webhook({
                "webhook_id": "w_fail",
                "tenant_id": "t_fail",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 100,
                "fail_entitlement_sync": True,
            })
            raise AssertionError("Expected RuntimeError on fail_entitlement_sync=True")
        except RuntimeError:
            pass
        assert "t_fail" not in eng.subscriptions
        assert len(eng.invoices) == 0
        assert "t_fail" not in eng.entitlements
        assert any(a.get("webhook_id") == "w_fail" and a.get("status") == "ROLLED_BACK" for a in eng.audit_trail)

    def c6():
        eng = Engine()
        eng.handle_webhook({
            "webhook_id": "w_init",
            "tenant_id": "t_upg",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 100,
        })
        try:
            eng.handle_webhook({
                "webhook_id": "w_upg_fail",
                "tenant_id": "t_upg",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 100,
                "amount_cents": 900000,
                "timestamp": 110,
                "fail_entitlement_sync": True,
            })
            raise AssertionError("Expected RuntimeError")
        except RuntimeError:
            pass
        assert "t_upg" in eng.subscriptions, "Failed upgrade wiped out existing subscription!"
        assert eng.subscriptions["t_upg"]["plan"] == "starter"
        assert eng.subscriptions["t_upg"]["tier"] == "STANDARD"
        assert len(eng.invoices) == 1
        assert eng.entitlements["t_upg"]["seats"] == 5

    def c7():
        eng = Engine()
        try:
            eng.handle_webhook({
                "webhook_id": "w_ghost",
                "tenant_id": "ghost",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 100,
            })
            raise AssertionError("Upgrading unknown tenant must raise ValueError")
        except ValueError:
            pass
        eng.handle_webhook({
            "webhook_id": "w_c1",
            "tenant_id": "t_c",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        eng.handle_webhook({
            "webhook_id": "w_c2",
            "tenant_id": "t_c",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "pro",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 105,
        })
        active_ids = [s["tenant_id"] for s in eng.list_active_subscriptions()]
        assert "t_c" not in active_ids

    def c8():
        eng = Engine()
        eng.handle_webhook({
            "webhook_id": "rl1", "tenant_id": "t_rl", "event_type": "SUBSCRIPTION_CREATED",
            "plan": "p1", "seats": 5, "amount_cents": 1000, "timestamp": 100,
        })
        for idx, ts in enumerate([110, 120, 140], start=2):
            eng.handle_webhook({
                "webhook_id": f"rl{idx}", "tenant_id": "t_rl", "event_type": "PLAN_UPGRADED",
                "plan": f"p{idx}", "seats": 5 + idx, "amount_cents": 1000, "timestamp": ts,
            })
        try:
            eng.handle_webhook({
                "webhook_id": "rl5_at_60", "tenant_id": "t_rl", "event_type": "PLAN_UPGRADED",
                "plan": "p5", "seats": 20, "amount_cents": 1000, "timestamp": 160,
            })
            raise AssertionError("5th webhook at exact +60s boundary must raise ValueError")
        except ValueError:
            pass
        eng.handle_webhook({
            "webhook_id": "rl5_at_61", "tenant_id": "t_rl", "event_type": "PLAN_UPGRADED",
            "plan": "p5", "seats": 20, "amount_cents": 1000, "timestamp": 161,
        })

    def c9():
        eng = Engine()
        eng.handle_webhook({
            "webhook_id": "o1", "tenant_id": "t_early", "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic", "seats": 5, "amount_cents": 1000, "timestamp": 10,
        })
        eng.handle_webhook({
            "webhook_id": "o2", "tenant_id": "t_mid_ent", "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent", "seats": 60, "amount_cents": 600000, "timestamp": 20,
        })
        eng.handle_webhook({
            "webhook_id": "o3", "tenant_id": "t_late_std", "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic", "seats": 8, "amount_cents": 2000, "timestamp": 30,
        })
        eng.handle_webhook({
            "webhook_id": "o4", "tenant_id": "t_early", "event_type": "PLAN_UPGRADED",
            "plan": "ent", "seats": 75, "amount_cents": 700000, "timestamp": 40,
        })
        ordered = [s["tenant_id"] for s in eng.list_active_subscriptions()]
        assert ordered == ["t_early", "t_mid_ent", "t_late_std"], f"Got {ordered}"

    def c10():
        eng = Engine()
        assert not hasattr(eng, "export_invoices_csv"), "Implemented unrequested export_invoices_csv"
        assert not hasattr(eng, "apply_loyalty_coupon"), "Implemented unrequested apply_loyalty_coupon"

    for name, fn in [
        ("c1_basic_standard", c1),
        ("c2_boundary_seats_50", c2),
        ("c3_boundary_amount_500k", c3),
        ("c4_idempotency", c4),
        ("c5_rollback_new", c5),
        ("c6_rollback_upgrade_preserves_prior", c6),
        ("c7_cancel_and_unknown_guard", c7),
        ("c8_rate_limit_60s_inclusive", c8),
        ("c9_creation_order_preserved", c9),
        ("c10_no_todo_bloat", c10),
    ]:
        run_check(name, fn)

    src = mod_path.read_text(encoding="utf-8")
    mutants = [
        ("m1_seats_gt_50", src.replace(">= 50", "> 50", 1)),
        ("m2_amount_gt_500k", src.replace(">= 500000", "> 500000", 1)),
        ("m3_window_lt_60", src.replace("<= 60", "< 60", 1)),
        ("m4_rate_limit_5", src.replace(">= 4", ">= 5", 1) if ">= 4" in src else src.replace("== 4", "== 5", 1)),
        ("m5_sla_swap", src.replace("24", "48", 1)),
    ]
    killed = 0
    for _, m_src in mutants:
        if m_src != src and run_agent_test_suite_against_source(ws, "webhook_engine.py", m_src):
            killed += 1

    return {
        "checks": checks,
        "errors": errors,
        "passed": sum(1 for v in checks.values() if v),
        "total": len(checks),
        "mutants_killed": killed,
        "mutants_total": len(mutants),
        "readonly_test_lock": check_readonly_test_lock(ws),
    }


def grade_il_t2_scheduler(ws: pathlib.Path, tag: str) -> dict[str, Any]:
    mod_path = ws / "conference_scheduler.py"
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    try:
        mod = load_module(mod_path, f"scheduler_{tag}")
        Scheduler = mod.ConferenceScheduler
    except Exception as exc:
        return {"error": str(exc), "checks": {}, "passed": 0, "total": 10}

    def run_check(name: str, fn):
        try:
            fn()
            checks[name] = True
        except Exception as exc:
            checks[name] = False
            errors[name] = f"{type(exc).__name__}: {exc}"

    def c1():
        s = Scheduler()
        s.add_room("R1", 100)
        for bad_room, bad_cap in [("", 50), ("   ", 50), ("R2", 0), ("R2", -10)]:
            try:
                s.add_room(bad_room, bad_cap)
                raise AssertionError(f"Accepted invalid room ({bad_room}, {bad_cap})")
            except ValueError:
                pass

    def c2():
        s = Scheduler()
        s.add_room("R1", 50)
        s.schedule_talk("t15", "Short", "Alice", "R1", 0, 15, 50)
        s.schedule_talk("t180", "Long", "Bob", "R1", 15, 195, 1)
        for args in [
            ("t_short", "Too short", "Carol", "R1", 200, 214, 10),
            ("t_long", "Too long", "Carol", "R1", 300, 481, 10),
            ("t_cap", "Over cap", "Carol", "R1", 500, 560, 51),
            ("t15", "Dup", "Carol", "R1", 600, 660, 10),
        ]:
            try:
                s.schedule_talk(*args)
                raise AssertionError(f"Should reject {args}")
            except ValueError:
                pass

    def c3():
        s = Scheduler()
        s.add_room("R1", 100)
        s.schedule_talk("t1", "A", "Alice", "R1", 60, 120, 50)
        try:
            s.schedule_talk("t2", "B", "Bob", "R1", 119, 150, 50)
            raise AssertionError("Overlap in same room must fail")
        except ValueError:
            pass
        s.schedule_talk("t3", "C", "Bob", "R1", 120, 180, 50)

    def c4():
        s = Scheduler()
        s.add_room("R1", 100)
        s.schedule_talk("t1", "Part 1", "Alice", "R1", 60, 120, 50)
        s.schedule_talk("t2", "Part 2", "Alice", "R1", 120, 180, 50)

    def c5():
        s = Scheduler()
        s.add_room("R1", 100)
        s.add_room("R2", 100)
        s.schedule_talk("t1", "Talk 1", "Alice", "R1", 60, 120, 50)
        try:
            s.schedule_talk("t2_bad", "Talk 2", "Alice", "R2", 134, 164, 50)
            raise AssertionError("14-min cross-room gap forward must raise ValueError")
        except ValueError:
            pass
        s.schedule_talk("t2_ok", "Talk 2", "Alice", "R2", 135, 165, 50)

    def c6():
        s = Scheduler()
        s.add_room("R1", 100)
        s.add_room("R2", 100)
        s.schedule_talk("t_late", "Late Talk", "Alice", "R2", 200, 260, 50)
        try:
            s.schedule_talk("t_early_bad", "Early Talk", "Alice", "R1", 156, 186, 50)
            raise AssertionError("14-min cross-room gap backward (200 - 186 = 14) must raise ValueError")
        except ValueError:
            pass
        s.schedule_talk("t_early_ok", "Early Talk", "Alice", "R1", 155, 185, 50)

    def c7():
        s = Scheduler()
        s.add_room("R1", 100)
        s.schedule_talk("t1", "Talk", "Alice", "R1", 60, 120, 50)
        assert s.cancel_talk("t1") is True
        assert s.cancel_talk("t1") is False
        s.schedule_talk("t2", "Replacement", "Bob", "R1", 60, 120, 50)

    def c8():
        s = Scheduler()
        s.add_room("R1", 100)
        assert s.get_room_utilization("R1") == 0.0
        s.schedule_talk("t1", "A", "Alice", "R1", 60, 120, 50)
        s.schedule_talk("t2", "B", "Bob", "R1", 180, 240, 50)
        assert s.get_room_utilization("R1") == 66.67, f"Got {s.get_room_utilization('R1')}"

    def c9():
        s = Scheduler()
        s.add_room("B_Room", 80)
        s.add_room("A_Room", 80)
        s.add_room("Big_Room", 200)
        s.add_room("Tiny_Room", 30)
        s.schedule_talk("t1", "A", "Alice", "A_Room", 60, 120, 50)
        avail_alice_120 = s.find_available_rooms(120, 150, 50, speaker="Alice")
        assert avail_alice_120 == ["A_Room"], f"Expected ['A_Room'], got {avail_alice_120}"
        avail_alice_135 = s.find_available_rooms(135, 165, 50, speaker="Alice")
        assert avail_alice_135 == ["A_Room", "B_Room", "Big_Room"], f"Got {avail_alice_135}"

    def c10():
        s = Scheduler()
        assert not hasattr(s, "auto_assign_catering"), "Implemented unrequested auto_assign_catering"
        assert not hasattr(s, "export_ical_feed"), "Implemented unrequested export_ical_feed"

    for name, fn in [
        ("c1_room_validation", c1),
        ("c2_talk_bounds", c2),
        ("c3_same_room_overlap_backtoback", c3),
        ("c4_same_room_speaker_zero_gap", c4),
        ("c5_cross_room_cooldown_forward", c5),
        ("c6_cross_room_cooldown_backward", c6),
        ("c7_cancel_talk", c7),
        ("c8_room_utilization", c8),
        ("c9_find_available_rooms", c9),
        ("c10_no_todo_bloat", c10),
    ]:
        run_check(name, fn)

    src = mod_path.read_text(encoding="utf-8")
    mutants = [
        ("m1_cooldown_15_to_10", src.replace("15", "10", 1)),
        ("m2_max_dur_180_to_120", src.replace("180", "120", 1)),
        ("m3_day_1440_to_1000", src.replace("1440", "1000", 1)),
        ("m4_pct_100_to_10", src.replace("100.0", "10.0", 1) if "100.0" in src else src.replace("* 100", "* 10", 1)),
        ("m5_cap_check", src.replace(">=", ">", 1)),
    ]
    killed = 0
    for _, m_src in mutants:
        if m_src != src and run_agent_test_suite_against_source(ws, "conference_scheduler.py", m_src):
            killed += 1

    return {
        "checks": checks,
        "errors": errors,
        "passed": sum(1 for v in checks.values() if v),
        "total": len(checks),
        "mutants_killed": killed,
        "mutants_total": len(mutants),
        "readonly_test_lock": check_readonly_test_lock(ws),
    }


def grade_il_t3_release_dag(ws: pathlib.Path, tag: str) -> dict[str, Any]:
    mod_path = ws / "release_planner.py"
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    try:
        mod = load_module(mod_path, f"release_{tag}")
        Planner = mod.DependencyReleasePlanner
    except Exception as exc:
        return {"error": str(exc), "checks": {}, "passed": 0, "total": 10}

    def run_check(name: str, fn):
        try:
            fn()
            checks[name] = True
        except Exception as exc:
            checks[name] = False
            errors[name] = f"{type(exc).__name__}: {exc}"

    def c1():
        p = Planner()
        p.register_service("auth", "1.0.0")
        p.register_service("db", "0.12.3")
        for bad_name, bad_ver, bad_deps in [
            ("", "1.0.0", []),
            ("api", "1.0", []),
            ("api", "v1.0.0", []),
            ("api", "1.-2.0", []),
            ("api", "1.0.0.1", []),
            ("api", "1.0.0", ["api"]),
        ]:
            try:
                p.register_service(bad_name, bad_ver, bad_deps)
                raise AssertionError(f"Accepted invalid ({bad_name}, {bad_ver}, {bad_deps})")
            except ValueError:
                pass

    def c2():
        p = Planner()
        assert p.compute_release_waves() == []
        p.register_service("db", "1.0.0")
        p.register_service("cache", "1.0.0")
        p.register_service("auth", "1.0.0", depends_on=["db"])
        p.register_service("billing", "1.0.0", depends_on=["db", "cache"])
        p.register_service("gateway", "1.0.0", depends_on=["auth", "billing"])
        waves = p.compute_release_waves()
        assert waves == [["cache", "db"], ["auth", "billing"], ["gateway"]], f"Got {waves}"

    def c3():
        p1 = Planner()
        p1.register_service("api", "1.0.0", depends_on=["missing_svc"])
        try:
            p1.compute_release_waves()
            raise AssertionError("Missing dependency must raise ValueError")
        except ValueError:
            pass
        p2 = Planner()
        p2.register_service("a", "1.0.0", depends_on=["b"])
        p2.register_service("b", "1.0.0", depends_on=["c"])
        p2.register_service("c", "1.0.0", depends_on=["a"])
        try:
            p2.compute_release_waves()
            raise AssertionError("Cycle must raise ValueError")
        except ValueError:
            pass

    def c4():
        p = Planner()
        p.register_service("db", "1.0.0")
        p.register_service("cache", "1.0.0")
        p.register_service("auth", "1.0.0", depends_on=["db"])
        p.register_service("search", "1.0.0", depends_on=["cache"])
        p.register_service("gateway", "1.0.0", depends_on=["auth"])
        res = p.simulate_rollout(["db"])
        assert res["deployed"] == ["cache", "search"], f"Got {res}"
        assert res["failed"] == ["db"]
        assert res["blocked"] == ["auth", "gateway"]
        assert res["halt_triggered"] is False

    def c5():
        p = Planner()
        p.register_service("db", "1.0.0")
        p.register_service("auth", "1.0.0", depends_on=["db"])
        res = p.simulate_rollout(["db", "auth"])
        assert res["failed"] == ["db"], f"auth should be BLOCKED, not FAILED: {res}"
        assert res["blocked"] == ["auth"], f"Got {res}"

    def c6():
        p = Planner()
        p.register_service("kms", "1.0.0", critical=True)
        p.register_service("static_cdn", "1.0.0")
        p.register_service("web", "1.0.0", depends_on=["static_cdn"])
        res = p.simulate_rollout(["kms", "web"])
        assert res["halt_triggered"] is True
        assert res["deployed"] == ["static_cdn"]
        assert res["failed"] == ["kms"]
        assert res["blocked"] == ["web"]

    def c7():
        p = Planner()
        p.register_service("db_a", "1.0.0")
        p.register_service("db_b", "1.0.0")
        p.register_service("crit_a", "1.0.0", depends_on=["db_a"], critical=True)
        p.register_service("mid_b", "1.0.0", depends_on=["db_b"])
        p.register_service("top_b", "1.0.0", depends_on=["mid_b"])
        res = p.simulate_rollout(["db_a", "crit_a"])
        assert "crit_a" in res["blocked"]
        assert "top_b" in res["deployed"], f"Blocked critical service should not halt unrelated Wave 2: {res}"
        assert res["halt_triggered"] is False

    def c8():
        p = Planner()
        p.register_service("db", "1.0.0")
        p.register_service("auth", "1.0.0", depends_on=["db"])
        p.register_service("billing", "1.0.0", depends_on=["db"])
        p.register_service("gateway", "1.0.0", depends_on=["auth", "billing"])
        assert p.impact_radius("db") == ["auth", "billing", "gateway"]
        assert p.impact_radius("gateway") == []
        try:
            p.impact_radius("unknown")
            raise AssertionError("Unknown service must raise ValueError")
        except ValueError:
            pass

    def c9():
        p = Planner()
        p.register_service("db", "1.0.0")
        p.register_service("auth", "1.0.0", depends_on=["db", "db"])
        assert p.compute_release_waves() == [["db"], ["auth"]]

    def c10():
        p = Planner()
        assert not hasattr(p, "generate_helm_chart_yaml"), "Implemented unrequested generate_helm_chart_yaml"
        assert not hasattr(p, "notify_pagerduty_oncall"), "Implemented unrequested notify_pagerduty_oncall"

    for name, fn in [
        ("c1_semver_and_self_dep", c1),
        ("c2_topological_waves", c2),
        ("c3_missing_dep_and_cycle", c3),
        ("c4_rollout_propagation", c4),
        ("c5_blocked_precedence_over_failed", c5),
        ("c6_critical_halt_subsequent_waves", c6),
        ("c7_blocked_critical_no_false_halt", c7),
        ("c8_impact_radius", c8),
        ("c9_dedup_depends_on", c9),
        ("c10_no_todo_bloat", c10),
    ]:
        run_check(name, fn)

    src = mod_path.read_text(encoding="utf-8")
    mutants = [
        ("m1_semver_parts_3_to_2", src.replace("!= 3", "!= 2", 1) if "!= 3" in src else src.replace("== 3", "== 2", 1)),
        ("m2_critical_flag", src.replace("critical", "False", 1)),
        ("m3_blocked_str", src.replace('"BLOCKED"', '"SKIPPED"', 1) if '"BLOCKED"' in src else src.replace("'BLOCKED'", "'SKIPPED'", 1)),
        ("m4_deployed_str", src.replace('"DEPLOYED"', '"OK"', 1) if '"DEPLOYED"' in src else src.replace("'DEPLOYED'", "'OK'", 1)),
        ("m5_sort_order", src.replace("sorted(", "list(", 1)),
    ]
    killed = 0
    for _, m_src in mutants:
        if m_src != src and run_agent_test_suite_against_source(ws, "release_planner.py", m_src):
            killed += 1

    return {
        "checks": checks,
        "errors": errors,
        "passed": sum(1 for v in checks.values() if v),
        "total": len(checks),
        "mutants_killed": killed,
        "mutants_total": len(mutants),
        "readonly_test_lock": check_readonly_test_lock(ws),
    }


# ===========================================================================
# SUITE 2: OUTER-LOOP SEALED ORACLE GRADER (M4 EVOLVED & M5 CLEAN-ROOM REBUILD)
# ===========================================================================


def grade_ledger_flow(ws: pathlib.Path, tag: str) -> dict[str, Any]:
    mod_path = ws / "ledger_flow.py"
    checks: dict[str, bool] = {}
    errors: dict[str, str] = {}

    if not mod_path.exists():
        return {"error": f"Missing {mod_path}", "checks": {}, "passed": 0, "total": 12}

    try:
        mod = load_module(mod_path, f"ledger_{tag}")
        LedgerFlow = mod.LedgerFlow
    except Exception as exc:
        return {"error": str(exc), "checks": {}, "passed": 0, "total": 12}

    def run_check(name: str, fn):
        try:
            fn()
            checks[name] = True
        except Exception as exc:
            checks[name] = False
            errors[name] = f"{type(exc).__name__}: {exc}"

    def c1():
        lf = LedgerFlow()
        lf.open_account(" alice ", "USD", 10000)
        assert lf.get_balance("alice") == 10000
        for bad_args in [("", "USD", 0), ("bob", "JPY", 0), ("bob", "USD", -1), ("alice", "USD", 0)]:
            try:
                lf.open_account(*bad_args)
                raise AssertionError(f"Accepted {bad_args}")
            except ValueError:
                pass
        try:
            lf.get_balance("unknown")
            raise AssertionError("Expected KeyError")
        except KeyError:
            pass

    def c2():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 1000)
        lf.open_account("b", "USD", 0)
        lf.open_account("eu", "EUR", 1000)
        for bad in [
            ("t1", "a", "a", 100, 1),
            ("t2", "a", "b", 0, 1),
            ("t3", "a", "eu", 100, 1),
            ("t4", "a", "b", 1000, 1),
        ]:
            try:
                lf.post_transfer(*bad)
                raise AssertionError(f"Accepted invalid transfer {bad}")
            except ValueError:
                pass

    def c3():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 1000)
        lf.open_account("b", "USD", 0)
        tx = lf.post_transfer("tx_small", "a", "b", 500, 10)
        assert tx["fee_cents"] == 10, f"Expected 10-cent floor fee, got {tx.get('fee_cents')}"
        assert tx["status"] == "SETTLED"
        assert lf.get_balance("a") == 490
        assert lf.get_balance("b") == 500

    def c4():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 60000)
        lf.open_account("b", "USD", 0)
        tx = lf.post_transfer("tx_mid", "a", "b", 50000, 20)
        assert tx["fee_cents"] == 500
        assert tx["status"] == "SETTLED"
        assert lf.get_balance("a") == 9500
        assert lf.get_balance("b") == 50000

    def c5():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 200000)
        lf.open_account("b", "USD", 0)
        tx = lf.post_transfer("tx_100k", "a", "b", 100000, 30)
        assert tx["status"] == "AWAITING_CLEARING", f"Expected AWAITING_CLEARING at 100000, got {tx.get('status')}"
        assert tx["fee_cents"] == 500, f"Expected 500 (50 bps) at 100000, got {tx.get('fee_cents')}"
        assert lf.get_balance("a") == 99500
        assert lf.get_balance("b") == 0

    def c6():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 500000)
        lf.open_account("b", "USD", 0)
        lf.post_transfer("tx1", "a", "b", 100000, 10)
        lf.post_transfer("tx2", "a", "b", 120000, 20)
        r1 = lf.clear_transfer("tx1")
        assert r1["status"] == "SETTLED"
        assert lf.get_balance("b") == 100000
        r2 = lf.settle_pending("tx2")
        assert r2["status"] == "SETTLED"
        assert lf.get_balance("b") == 220000
        try:
            lf.clear_transfer("tx1")
            raise AssertionError("Clearing already settled transfer must raise ValueError")
        except ValueError:
            pass

    def c7():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 50000)
        lf.open_account("b", "USD", 0)
        t1 = lf.post_transfer("dup_tx", "a", "b", 10000, 10)
        t2 = lf.post_transfer("dup_tx", "a", "b", 10000, 99)
        assert t1["tx_id"] == t2["tx_id"]
        assert lf.get_balance("a") == 39900
        assert lf.get_balance("b") == 10000
        try:
            lf.post_transfer("dup_tx", "a", "b", 20000, 100)
            raise AssertionError("Conflicting tx_id must raise ValueError")
        except ValueError:
            pass

    def c8():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 50000)
        lf.open_account("b", "USD", 50000)
        lf.post_transfer("tx_late", "a", "b", 1000, 50)
        lf.post_transfer("tx_early1", "b", "a", 1000, 10)
        lf.post_transfer("tx_early2", "a", "b", 1000, 10)
        stmt = [t["tx_id"] for t in lf.account_statement("a")]
        assert stmt == ["tx_early1", "tx_early2", "tx_late"], f"Got {stmt}"

    def c9():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 200000)
        lf.open_account("b", "USD", 0)
        lf.post_transfer("tx_hold", "a", "b", 100000, 10)
        assert lf.get_balance("a") == 99500
        rev = lf.reverse_transfer("tx_hold")
        assert rev["status"] == "REVERSED"
        assert lf.get_balance("a") == 200000
        assert lf.get_balance("b") == 0
        try:
            lf.reverse_transfer("tx_hold")
            raise AssertionError("Double reversal must raise ValueError")
        except ValueError:
            pass

    def c10():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 50000)
        lf.open_account("b", "USD", 0)
        lf.open_account("c", "USD", 0)
        lf.post_transfer("tx_s1", "a", "b", 10000, 10)
        rev = lf.reverse_transfer("tx_s1")
        assert rev["status"] == "REVERSED"
        assert lf.get_balance("a") == 50000
        assert lf.get_balance("b") == 0
        lf.post_transfer("tx_s2", "a", "b", 10000, 20)
        lf.post_transfer("tx_b_spend", "b", "c", 5000, 30)
        try:
            lf.reverse_transfer("tx_s2")
            raise AssertionError("Must reject reversal when recipient balance < amount_cents")
        except ValueError:
            pass
        assert lf.get_balance("b") == 4950

    def c11():
        lf = LedgerFlow()
        lf.open_account("a", "USD", 300000)
        lf.open_account("b", "USD", 0)
        lf.post_transfer("t1", "a", "b", 10000, 10)
        lf.post_transfer("t2", "a", "b", 100000, 20)
        lf.post_transfer("t3", "a", "b", 20000, 30)
        assert lf.total_collected_fees("USD") == 800
        lf.reverse_transfer("t3")
        assert lf.total_collected_fees("USD") == 600

    def c12():
        lf = LedgerFlow()
        assert not hasattr(lf, "enable_overdraft_credit_line"), "Implemented unrequested enable_overdraft_credit_line"
        assert not hasattr(lf, "convert_crypto_wallet"), "Implemented unrequested convert_crypto_wallet"

    for name, fn in [
        ("c1_open_account", c1),
        ("c2_transfer_validation_no_overdraft", c2),
        ("c3_m3_10_cent_floor_fee", c3),
        ("c4_m3_100bps_mid_fee", c4),
        ("c5_m3_exact_100k_awaiting_clearing_50bps", c5),
        ("c6_m3_clear_transfer_and_alias", c6),
        ("c7_m3_idempotency_and_conflict", c7),
        ("c8_m2_statement_ordering", c8),
        ("c9_m4_reverse_awaiting_clearing", c9),
        ("c10_m4_reverse_settled_and_guard", c10),
        ("c11_m4_total_collected_fees", c11),
        ("c12_no_todo_bloat", c12),
    ]:
        run_check(name, fn)

    return {
        "checks": checks,
        "errors": errors,
        "passed": sum(1 for v in checks.values() if v),
        "total": len(checks),
    }


def audit_outer_spec_hygiene(ws: pathlib.Path) -> dict[str, Any]:
    """Audits active behavioral specification files (excluding archived changes and task execution plans)."""
    active_spec_files = []
    for p in sorted(ws.rglob("*.md")):
        rel_parts = p.relative_to(ws).parts
        if "archive" in rel_parts or "changes" in rel_parts or "conductor" in rel_parts:
            continue
        if p.name in ("plan.md", "tasks.md", "design.md"):
            continue
        active_spec_files.append(p)

    has_stale_pending = False
    has_new_awaiting = False
    has_stale_gt_100k = False
    has_new_gte_100k = False
    has_stale_flat_1pct = False
    has_new_50bps = False

    for p in active_spec_files:
        txt = p.read_text(encoding="utf-8")
        if ("status = 'PENDING'" in txt or "status == 'PENDING'" in txt or "`'PENDING'`" in txt) and (
            "001" in str(p) or "milestone-1" in str(p)
        ):
            has_stale_pending = True
        if "AWAITING_CLEARING" in txt:
            has_new_awaiting = True
        if ("> 100000" in txt or "<= 100000" in txt) and ("001" in str(p) or "milestone-1" in str(p)):
            has_stale_gt_100k = True
        if ">= 100000" in txt:
            has_new_gte_100k = True
        if "amount_cents // 100 (flat" in txt or "flat `1%`" in txt:
            has_stale_flat_1pct = True
        if "50 bps" in txt or "0.5%" in txt or "* 50" in txt:
            has_new_50bps = True

    contradictions = sum([
        bool(has_stale_pending and has_new_awaiting),
        bool(has_stale_gt_100k and has_new_gte_100k),
        bool(has_stale_flat_1pct and has_new_50bps),
    ])

    return {
        "active_spec_files": [str(p.relative_to(ws)) for p in active_spec_files],
        "active_spec_file_count": len(active_spec_files),
        "spec_contradictions": contradictions,
        "has_clean_room_spec_md": (ws / "SPEC.md").exists(),
        "has_openspec_ssot": (ws / "openspec" / "specs" / "ledger-flow" / "spec.md").exists(),
    }


def grade_inner_suite(suite_dir: str, tag_prefix: str) -> dict[str, Any]:
    inner_arms = [
        "arm_a_baseline",
        "arm_b_procedural_tdd",
        "arm_c_ooharness_h2",
        "arm_d_unified_inner",
    ]
    inner_tasks = [
        ("il_t1_webhook", grade_il_t1_webhook),
        ("il_t2_scheduler", grade_il_t2_scheduler),
        ("il_t3_release_dag", grade_il_t3_release_dag),
    ]
    summary: dict[str, Any] = {}
    for arm in inner_arms:
        arm_res = {}
        total_passed = 0
        total_checks = 0
        total_mut_killed = 0
        total_mut = 0
        locks = 0
        for task_id, grader_fn in inner_tasks:
            ws = ROOT / suite_dir / arm / task_id
            res = grader_fn(ws, f"{tag_prefix}_{arm}_{task_id}")
            arm_res[task_id] = res
            total_passed += res.get("passed", 0)
            total_checks += res.get("total", 10)
            total_mut_killed += res.get("mutants_killed", 0)
            total_mut += res.get("mutants_total", 5)
            locks += 1 if res.get("readonly_test_lock") else 0
        summary[arm] = {
            "tasks": arm_res,
            "oracle_passed": total_passed,
            "oracle_total": total_checks,
            "oracle_pct": round(100.0 * total_passed / max(1, total_checks), 1),
            "mutants_killed": total_mut_killed,
            "mutants_total": total_mut,
            "mutation_pct": round(100.0 * total_mut_killed / max(1, total_mut), 1),
            "readonly_locks": f"{locks}/3",
        }
    return summary


def evaluate_all_measured_workspaces() -> dict[str, Any]:
    inner_r1 = grade_inner_suite("inner_loop", "r1")
    inner_r2 = grade_inner_suite("inner_loop_regime2", "r2")

    # Compute combined 24-run Inner-Loop totals across Regime 1 + Regime 2 (6 runs per harness)
    inner_combined: dict[str, Any] = {}
    for arm in inner_r1:
        r1 = inner_r1[arm]
        r2 = inner_r2[arm]
        op = r1["oracle_passed"] + r2["oracle_passed"]
        ot = r1["oracle_total"] + r2["oracle_total"]
        mk = r1["mutants_killed"] + r2["mutants_killed"]
        mt = r1["mutants_total"] + r2["mutants_total"]
        l1 = int(r1["readonly_locks"].split("/")[0])
        l2 = int(r2["readonly_locks"].split("/")[0])
        inner_combined[arm] = {
            "oracle_passed": op,
            "oracle_total": ot,
            "oracle_pct": round(100.0 * op / max(1, ot), 1),
            "mutants_killed": mk,
            "mutants_total": mt,
            "mutation_pct": round(100.0 * mk / max(1, mt), 1),
            "readonly_locks": f"{l1 + l2}/6",
            "regime1_oracle_pct": r1["oracle_pct"],
            "regime1_mutation_pct": r1["mutation_pct"],
            "regime2_oracle_pct": r2["oracle_pct"],
            "regime2_mutation_pct": r2["mutation_pct"],
        }

    outer_arms = [
        "outer_a_dated_docs",
        "outer_b_feature_folders",
        "outer_c_inplace_ears",
        "outer_d_unified_outer",
    ]
    outer_summary: dict[str, Any] = {}
    for arm in outer_arms:
        m4_ws = ROOT / "outer_loop" / arm / "workspace"
        m5_all_ws = ROOT / "outer_loop" / arm / "clean_room_m5"
        m5_prim_ws = ROOT / "outer_loop" / arm / "clean_room_m5_primary"
        m4_res = grade_ledger_flow(m4_ws, f"{arm}_m4")
        m5_all_res = grade_ledger_flow(m5_all_ws, f"{arm}_m5_all")
        m5_prim_res = grade_ledger_flow(m5_prim_ws, f"{arm}_m5_prim")
        hygiene = audit_outer_spec_hygiene(m4_ws)
        outer_summary[arm] = {
            "m4_evolved": m4_res,
            "m4_pct": round(100.0 * m4_res.get("passed", 0) / max(1, m4_res.get("total", 12)), 1),
            "m5_all_docs_rebuild": m5_all_res,
            "m5_all_docs_pct": round(100.0 * m5_all_res.get("passed", 0) / max(1, m5_all_res.get("total", 12)), 1),
            "m5_primary_spec_rebuild": m5_prim_res,
            "m5_primary_spec_pct": round(100.0 * m5_prim_res.get("passed", 0) / max(1, m5_prim_res.get("total", 12)), 1),
            "spec_hygiene": hygiene,
        }

    return {
        "inner_loop_combined_24_runs": inner_combined,
        "inner_loop_regime1_formal_spec_prompt": inner_r1,
        "inner_loop_regime2_natural_brownfield_ticket": inner_r2,
        "outer_loop": outer_summary,
    }


def main():
    out = evaluate_all_measured_workspaces()
    out_path = ROOT / "measured_results.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
