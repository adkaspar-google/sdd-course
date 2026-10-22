"""Unit tests for SubscriptionWebhookEngine."""

from __future__ import annotations
import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def test_enterprise_tier_boundaries_50_seats_and_500000_cents(self) -> None:
        res_seats_50 = self.engine.handle_webhook({
            "webhook_id": "wh-1",
            "tenant_id": "t-seats-50",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro-50",
            "seats": 50,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        self.assertEqual(res_seats_50["tier"], "ENTERPRISE")
        self.assertEqual(res_seats_50["sla_hours"], 1)

        res_seats_49 = self.engine.handle_webhook({
            "webhook_id": "wh-2",
            "tenant_id": "t-seats-49",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro-49",
            "seats": 49,
            "amount_cents": 499999,
            "timestamp": 100,
        })
        self.assertEqual(res_seats_49["tier"], "STANDARD")
        self.assertEqual(res_seats_49["sla_hours"], 24)

        res_amount_500k = self.engine.handle_webhook({
            "webhook_id": "wh-3",
            "tenant_id": "t-amount-500k",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent-5k",
            "seats": 10,
            "amount_cents": 500000,
            "timestamp": 100,
        })
        self.assertEqual(res_amount_500k["tier"], "ENTERPRISE")
        self.assertEqual(res_amount_500k["sla_hours"], 1)

    def test_rate_limit_4_successful_webhooks_in_60s_window(self) -> None:
        self.engine.handle_webhook({
            "webhook_id": "wh-1",
            "tenant_id": "t-1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 100,
        })
        # Failed webhook should not count toward the 4-webhook limit
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh-fail",
                "tenant_id": "t-1",
                "event_type": "PLAN_UPGRADED",
                "plan": "growth",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 105,
                "fail_entitlement_sync": True,
            })

        for i, ts in enumerate((110, 120, 130), start=2):
            self.engine.handle_webhook({
                "webhook_id": f"wh-{i}",
                "tenant_id": "t-1",
                "event_type": "PLAN_UPGRADED",
                "plan": f"plan-{i}",
                "seats": 5 + i,
                "amount_cents": 5000 * i,
                "timestamp": ts,
            })

        # 5th webhook within 60 seconds of timestamp 100 should fail
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-5",
                "tenant_id": "t-1",
                "event_type": "PLAN_UPGRADED",
                "plan": "plan-5",
                "seats": 20,
                "amount_cents": 25000,
                "timestamp": 159,
            })

        # At timestamp 160 (60s after first webhook at 100), another webhook is allowed
        res = self.engine.handle_webhook({
            "webhook_id": "wh-6",
            "tenant_id": "t-1",
            "event_type": "PLAN_UPGRADED",
            "plan": "plan-6",
            "seats": 25,
            "amount_cents": 30000,
            "timestamp": 160,
        })
        self.assertEqual(res["plan"], "plan-6")

    def test_upgrade_or_cancel_without_active_subscription_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-u1",
                "tenant_id": "nonexistent",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 100,
            })

        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-c1",
                "tenant_id": "nonexistent",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 100,
            })

        # Create then cancel, then attempt upgrade or second cancel
        self.engine.handle_webhook({
            "webhook_id": "wh-create",
            "tenant_id": "t-canceled",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 100,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh-cancel",
            "tenant_id": "t-canceled",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "basic",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 110,
        })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-upgrade-after-cancel",
                "tenant_id": "t-canceled",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 120,
            })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh-cancel-twice",
                "tenant_id": "t-canceled",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "basic",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 125,
            })

    def test_rollback_restores_previous_subscription_and_entitlement_on_upgrade_and_cancel(self) -> None:
        created = self.engine.handle_webhook({
            "webhook_id": "wh-init",
            "tenant_id": "t-rollback",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })

        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh-upgrade-fail",
                "tenant_id": "t-rollback",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 50,
                "amount_cents": 500000,
                "timestamp": 110,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t-rollback"], created)
        self.assertEqual(
            self.engine.entitlements["t-rollback"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.invoices[0]["webhook_id"], "wh-init")

        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh-cancel-fail",
                "tenant_id": "t-rollback",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "starter",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 120,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t-rollback"], created)
        self.assertEqual(
            self.engine.entitlements["t-rollback"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)

    def test_list_active_subscriptions_preserves_creation_order_on_upgrade(self) -> None:
        self.engine.handle_webhook({
            "webhook_id": "wh-t1",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "std-1",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh-t2",
            "tenant_id": "t2",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent-1",
            "seats": 50,
            "amount_cents": 500000,
            "timestamp": 110,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh-t3",
            "tenant_id": "t3",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "std-2",
            "seats": 20,
            "amount_cents": 20000,
            "timestamp": 120,
        })

        # Upgrade t1 to ENTERPRISE; t1 was created before t2 so t1 should appear before t2
        self.engine.handle_webhook({
            "webhook_id": "wh-t1-up",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "ent-upgraded",
            "seats": 60,
            "amount_cents": 600000,
            "timestamp": 130,
        })

        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["t1", "t2", "t3"])


if __name__ == "__main__":
    unittest.main()
