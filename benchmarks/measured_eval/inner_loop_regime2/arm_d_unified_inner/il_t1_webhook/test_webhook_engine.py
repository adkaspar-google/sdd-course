"""Unit tests for SubscriptionWebhookEngine."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def test_enterprise_exact_boundaries(self) -> None:
        # 50 seats -> ENTERPRISE (sla_hours=1)
        res_50 = self.engine.handle_webhook({
            "webhook_id": "wh-1",
            "tenant_id": "t-50",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 50,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        self.assertEqual(res_50["tier"], "ENTERPRISE")
        self.assertEqual(res_50["sla_hours"], 1)

        # 49 seats and 499999 cents -> STANDARD (sla_hours=24)
        res_49 = self.engine.handle_webhook({
            "webhook_id": "wh-2",
            "tenant_id": "t-49",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 49,
            "amount_cents": 499999,
            "timestamp": 100,
        })
        self.assertEqual(res_49["tier"], "STANDARD")
        self.assertEqual(res_49["sla_hours"], 24)

        # 500000 cents -> ENTERPRISE (sla_hours=1)
        res_500k = self.engine.handle_webhook({
            "webhook_id": "wh-3",
            "tenant_id": "t-500k",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "enterprise",
            "seats": 10,
            "amount_cents": 500000,
            "timestamp": 100,
        })
        self.assertEqual(res_500k["tier"], "ENTERPRISE")
        self.assertEqual(res_500k["sla_hours"], 1)

    def test_rate_limit_inclusive_60s_window_and_failed_calls_excluded(self) -> None:
        for i, ts in enumerate([100, 110, 120, 130]):
            self.engine.handle_webhook({
                "webhook_id": f"wh-rl-{i}",
                "tenant_id": "t-rate",
                "event_type": "SUBSCRIPTION_CREATED" if i == 0 else "PLAN_UPGRADED",
                "plan": f"p-{i}",
                "seats": 10 + i,
                "amount_cents": 1000,
                "timestamp": ts,
            })

        # At t=160 (160 - 100 == 60), still within inclusive 60s window -> rate limited
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-rl-block",
                "tenant_id": "t-rate",
                "event_type": "PLAN_UPGRADED",
                "plan": "p-block",
                "seats": 20,
                "amount_cents": 2000,
                "timestamp": 160,
            })

        # At t=161 (161 - 100 == 61 > 60), oldest call expired -> allowed
        # First test that a failed call at t=161 does not consume the rate limit slot
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh-rl-fail",
                "tenant_id": "t-rate",
                "event_type": "PLAN_UPGRADED",
                "plan": "p-fail",
                "seats": 25,
                "amount_cents": 2500,
                "timestamp": 161,
                "fail_entitlement_sync": True,
            })

        # Now succeed at t=161
        res_ok = self.engine.handle_webhook({
            "webhook_id": "wh-rl-ok",
            "tenant_id": "t-rate",
            "event_type": "PLAN_UPGRADED",
            "plan": "p-ok",
            "seats": 25,
            "amount_cents": 2500,
            "timestamp": 161,
        })
        self.assertEqual(res_ok["plan"], "p-ok")

    def test_upgrade_or_cancel_without_active_subscription_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-up-missing",
                "tenant_id": "t-none",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 1000,
                "timestamp": 10,
            })

        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-cancel-missing",
                "tenant_id": "t-none",
                "event_type": "SUBSCRIPTION_CANCELED",
                "timestamp": 10,
            })

        # Create then cancel, then attempt second cancel or upgrade on CANCELED subscription
        self.engine.handle_webhook({
            "webhook_id": "wh-c1",
            "tenant_id": "t-cancel",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 5,
            "amount_cents": 500,
            "timestamp": 10,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh-c2",
            "tenant_id": "t-cancel",
            "event_type": "SUBSCRIPTION_CANCELED",
            "timestamp": 20,
        })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-c3",
                "tenant_id": "t-cancel",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 1000,
                "timestamp": 30,
            })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-c4",
                "tenant_id": "t-cancel",
                "event_type": "SUBSCRIPTION_CANCELED",
                "timestamp": 35,
            })

    def test_rollback_restores_previous_subscription_and_entitlement(self) -> None:
        created = self.engine.handle_webhook({
            "webhook_id": "wh-init",
            "tenant_id": "t-rb",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        self.assertEqual(len(self.engine.invoices), 1)

        # Failed upgrade should restore prior subscription and entitlement
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh-up-fail",
                "tenant_id": "t-rb",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 60,
                "amount_cents": 600000,
                "timestamp": 110,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t-rb"], created)
        self.assertEqual(
            self.engine.entitlements["t-rb"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)

        # Failed cancel should also restore prior subscription and entitlement
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh-cancel-fail",
                "tenant_id": "t-rb",
                "event_type": "SUBSCRIPTION_CANCELED",
                "timestamp": 120,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t-rb"], created)
        self.assertEqual(
            self.engine.entitlements["t-rb"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )

    def test_list_active_subscriptions_preserves_creation_seq_across_upgrades(self) -> None:
        self.engine.handle_webhook({
            "webhook_id": "wh-t1-create",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 10,
            "amount_cents": 1000,
            "timestamp": 100,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh-t2-create",
            "tenant_id": "t2",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent",
            "seats": 50,
            "amount_cents": 500000,
            "timestamp": 105,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh-t3-create",
            "tenant_id": "t3",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 15,
            "amount_cents": 1500,
            "timestamp": 110,
        })

        # Upgrade t1 to ENTERPRISE -> t1 was created before t2, so t1 should come before t2
        self.engine.handle_webhook({
            "webhook_id": "wh-t1-upgrade",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "ent-plus",
            "seats": 50,
            "amount_cents": 200000,
            "timestamp": 120,
        })

        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["t1", "t2", "t3"])
        self.assertEqual(active[0]["seq"], 1)
        self.assertEqual(active[1]["seq"], 2)
        self.assertEqual(active[2]["seq"], 3)

    def test_out_of_scope_todos_not_implemented(self) -> None:
        self.assertFalse(hasattr(self.engine, "export_invoices_csv"))
        self.assertFalse(hasattr(self.engine, "apply_loyalty_coupon"))


if __name__ == "__main__":
    unittest.main()
