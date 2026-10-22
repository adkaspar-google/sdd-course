"""Unit tests for SubscriptionWebhookEngine."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def test_create_subscription_standard_and_enterprise_boundaries(self) -> None:
        # Standard tier: seats < 50 and amount_cents < 500000
        res_std = self.engine.handle_webhook({
            "webhook_id": "wh_1",
            "tenant_id": "t_std",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 49,
            "amount_cents": 499999,
            "timestamp": 100,
        })
        self.assertEqual(res_std["tier"], "STANDARD")
        self.assertEqual(res_std["sla_hours"], 24)
        self.assertEqual(res_std["status"], "ACTIVE")

        # Enterprise boundary by seats == 50
        res_ent_seats = self.engine.handle_webhook({
            "webhook_id": "wh_2",
            "tenant_id": "t_ent_seats",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 50,
            "amount_cents": 1000,
            "timestamp": 101,
        })
        self.assertEqual(res_ent_seats["tier"], "ENTERPRISE")
        self.assertEqual(res_ent_seats["sla_hours"], 1)

        # Enterprise boundary by amount_cents == 500000
        res_ent_amt = self.engine.handle_webhook({
            "webhook_id": "wh_3",
            "tenant_id": "t_ent_amt",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "enterprise",
            "seats": 10,
            "amount_cents": 500000,
            "timestamp": 102,
        })
        self.assertEqual(res_ent_amt["tier"], "ENTERPRISE")
        self.assertEqual(res_ent_amt["sla_hours"], 1)

    def test_idempotency_replay_safety(self) -> None:
        payload = {
            "webhook_id": "wh_idem_1",
            "tenant_id": "t_1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 100,
        }
        first = self.engine.handle_webhook(payload)
        first["plan"] = "mutated_by_caller"

        # Replay with modified payload fields but same webhook_id
        replay = self.engine.handle_webhook({
            **payload,
            "plan": "hacked",
            "seats": 100,
            "timestamp": 105,
        })
        self.assertEqual(replay["plan"], "starter")
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(len(self.engine.audit_trail), 1)
        self.assertEqual(self.engine.entitlements["t_1"]["seats"], 5)

    def test_validation_errors_leave_zero_state_changes(self) -> None:
        invalid_payloads = [
            # Unknown event_type
            {
                "webhook_id": "wh_v1",
                "tenant_id": "t1",
                "event_type": "UNKNOWN_EVENT",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 1000,
                "timestamp": 100,
            },
            # Blank webhook_id
            {
                "webhook_id": "   ",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 1000,
                "timestamp": 100,
            },
            # Blank tenant_id
            {
                "webhook_id": "wh_v2",
                "tenant_id": "",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 1000,
                "timestamp": 100,
            },
            # Negative amount_cents
            {
                "webhook_id": "wh_v3",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": -1,
                "timestamp": 100,
            },
            # seats <= 0 on SUBSCRIPTION_CREATED
            {
                "webhook_id": "wh_v4",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 1000,
                "timestamp": 100,
            },
            # Upgrading non-existent subscription
            {
                "webhook_id": "wh_v5",
                "tenant_id": "t_missing",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 2000,
                "timestamp": 100,
            },
            # Canceling non-existent subscription
            {
                "webhook_id": "wh_v6",
                "tenant_id": "t_missing",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 100,
            },
        ]
        for payload in invalid_payloads:
            with self.assertRaises(ValueError):
                self.engine.handle_webhook(payload)

        self.assertEqual(self.engine.subscriptions, {})
        self.assertEqual(self.engine.invoices, [])
        self.assertEqual(self.engine.entitlements, {})
        self.assertEqual(self.engine.audit_trail, [])

    def test_cancel_allows_zero_seats_and_blocks_subsequent_upgrade_or_cancel(self) -> None:
        self.engine.handle_webhook({
            "webhook_id": "wh_c1",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        res_cancel = self.engine.handle_webhook({
            "webhook_id": "wh_c2",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "pro",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 110,
        })
        self.assertEqual(res_cancel["status"], "CANCELED")
        self.assertEqual(self.engine.list_active_subscriptions(), [])

        # Upgrading or canceling an already-canceled subscription must raise ValueError
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_c3",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 50,
                "amount_cents": 500000,
                "timestamp": 120,
            })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_c4",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 125,
            })

    def test_transactional_rollback_restores_previous_state(self) -> None:
        self.engine.handle_webhook({
            "webhook_id": "wh_init",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })

        with self.assertRaises(RuntimeError) as ctx:
            self.engine.handle_webhook({
                "webhook_id": "wh_fail_upgrade",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 100,
                "amount_cents": 900000,
                "timestamp": 110,
                "fail_entitlement_sync": True,
            })
        self.assertIn("Entitlement service unavailable", str(ctx.exception))

        # Previous subscription, invoices, and entitlements must remain intact
        self.assertEqual(self.engine.subscriptions["t1"]["plan"], "starter")
        self.assertEqual(self.engine.subscriptions["t1"]["seats"], 10)
        self.assertEqual(self.engine.subscriptions["t1"]["tier"], "STANDARD")
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.entitlements["t1"], {"seats": 10, "tier": "STANDARD"})
        self.assertEqual(
            self.engine.audit_trail,
            [
                {"webhook_id": "wh_init", "status": "PROCESSED"},
                {"webhook_id": "wh_fail_upgrade", "status": "ROLLED_BACK"},
            ],
        )

    def test_sliding_window_rate_limit(self) -> None:
        # 1st at t=100 (create)
        self.engine.handle_webhook({
            "webhook_id": "wh_rl_1",
            "tenant_id": "t_rl",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "p1",
            "seats": 5,
            "amount_cents": 1000,
            "timestamp": 100,
        })
        # 2nd, 3rd, 4th within 60s window (t=120, 140, 160 -> 160 - 100 == 60 inclusive)
        for idx, ts in enumerate([120, 140, 160], start=2):
            self.engine.handle_webhook({
                "webhook_id": f"wh_rl_{idx}",
                "tenant_id": "t_rl",
                "event_type": "PLAN_UPGRADED",
                "plan": f"p{idx}",
                "seats": 5 + idx,
                "amount_cents": 1000 * idx,
                "timestamp": ts,
            })

        # Replay of an existing webhook at t=160 must NOT fail or count against rate limit
        replay = self.engine.handle_webhook({
            "webhook_id": "wh_rl_4",
            "tenant_id": "t_rl",
            "event_type": "PLAN_UPGRADED",
            "plan": "p4",
            "seats": 9,
            "amount_cents": 4000,
            "timestamp": 160,
        })
        self.assertEqual(replay["plan"], "p4")

        # 5th webhook at t=160 (within inclusive 60s of t=100) must raise ValueError('Rate limit exceeded')
        with self.assertRaisesRegex(ValueError, "Rate limit exceeded"):
            self.engine.handle_webhook({
                "webhook_id": "wh_rl_5_blocked",
                "tenant_id": "t_rl",
                "event_type": "PLAN_UPGRADED",
                "plan": "p5",
                "seats": 20,
                "amount_cents": 5000,
                "timestamp": 160,
            })
        self.assertEqual(self.engine.subscriptions["t_rl"]["plan"], "p4")
        self.assertEqual(len(self.engine.invoices), 4)

        # At t=161 (161 - 100 = 61 > 60), the t=100 event falls out of the window so a new webhook succeeds
        res_after_window = self.engine.handle_webhook({
            "webhook_id": "wh_rl_6_ok",
            "tenant_id": "t_rl",
            "event_type": "PLAN_UPGRADED",
            "plan": "p6",
            "seats": 25,
            "amount_cents": 6000,
            "timestamp": 161,
        })
        self.assertEqual(res_after_window["plan"], "p6")

    def test_list_active_subscriptions_ordering_and_upgrade_tie_breaking(self) -> None:
        # Create t1 (STANDARD, order 1), t2 (STANDARD, order 2), t3 (ENTERPRISE, order 3), t4 (STANDARD, order 4)
        self.engine.handle_webhook({
            "webhook_id": "w1",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 5,
            "amount_cents": 1000,
            "timestamp": 10,
        })
        self.engine.handle_webhook({
            "webhook_id": "w2",
            "tenant_id": "t2",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 10,
            "amount_cents": 2000,
            "timestamp": 20,
        })
        self.engine.handle_webhook({
            "webhook_id": "w3",
            "tenant_id": "t3",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent",
            "seats": 60,
            "amount_cents": 600000,
            "timestamp": 30,
        })
        self.engine.handle_webhook({
            "webhook_id": "w4",
            "tenant_id": "t4",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 15,
            "amount_cents": 3000,
            "timestamp": 40,
        })

        # Upgrade t1 within STANDARD tier -> should still appear before t2 and t4
        self.engine.handle_webhook({
            "webhook_id": "w5",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "plus",
            "seats": 20,
            "amount_cents": 4000,
            "timestamp": 50,
        })

        # Upgrade t2 to ENTERPRISE -> both t2 and t3 are ENTERPRISE, but t2 was originally created before t3!
        self.engine.handle_webhook({
            "webhook_id": "w6",
            "tenant_id": "t2",
            "event_type": "PLAN_UPGRADED",
            "plan": "ent",
            "seats": 50,
            "amount_cents": 100000,
            "timestamp": 60,
        })

        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["t2", "t3", "t1", "t4"])


if __name__ == "__main__":
    unittest.main()
