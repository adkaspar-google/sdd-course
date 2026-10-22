"""Unit tests for SubscriptionWebhookEngine."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def test_50_seats_gets_enterprise_tier(self) -> None:
        res = self.engine.handle_webhook({
            "webhook_id": "wh_1",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 50,
            "amount_cents": 10000,
            "timestamp": 1000,
        })
        self.assertEqual(res["tier"], "ENTERPRISE")
        self.assertEqual(res["sla_hours"], 1)
        self.assertEqual(self.engine.entitlements["tenant_a"]["tier"], "ENTERPRISE")

    def test_500000_cents_gets_enterprise_tier(self) -> None:
        res = self.engine.handle_webhook({
            "webhook_id": "wh_1",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 10,
            "amount_cents": 500000,
            "timestamp": 1000,
        })
        self.assertEqual(res["tier"], "ENTERPRISE")
        self.assertEqual(res["sla_hours"], 1)
        self.assertEqual(self.engine.entitlements["tenant_a"]["tier"], "ENTERPRISE")

    def test_below_50_seats_and_500000_cents_gets_standard_tier(self) -> None:
        res = self.engine.handle_webhook({
            "webhook_id": "wh_1",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 49,
            "amount_cents": 499999,
            "timestamp": 1000,
        })
        self.assertEqual(res["tier"], "STANDARD")
        self.assertEqual(res["sla_hours"], 24)

    def test_rate_limit_counts_only_successful_webhooks(self) -> None:
        # 1st successful webhook
        self.engine.handle_webhook({
            "webhook_id": "wh_1",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 1000,
        })
        # Failed webhook due to entitlement sync failure should NOT count toward rate limit
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh_fail_1",
                "tenant_id": "tenant_a",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 20,
                "amount_cents": 20000,
                "timestamp": 1005,
                "fail_entitlement_sync": True,
            })
        # 2nd, 3rd, and 4th successful webhooks within 60s window should all succeed
        for i in range(2, 5):
            self.engine.handle_webhook({
                "webhook_id": f"wh_{i}",
                "tenant_id": "tenant_a",
                "event_type": "PLAN_UPGRADED",
                "plan": f"pro_{i}",
                "seats": 10 + i,
                "amount_cents": 10000 * i,
                "timestamp": 1000 + i * 10,
            })
        # 5th webhook within 60s window should be rate limited
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_5",
                "tenant_id": "tenant_a",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro_5",
                "seats": 25,
                "amount_cents": 50000,
                "timestamp": 1050,
            })
        # Webhook at timestamp 1060 (60s after 1000) should succeed
        res = self.engine.handle_webhook({
            "webhook_id": "wh_6",
            "tenant_id": "tenant_a",
            "event_type": "PLAN_UPGRADED",
            "plan": "pro_6",
            "seats": 30,
            "amount_cents": 60000,
            "timestamp": 1060,
        })
        self.assertEqual(res["plan"], "pro_6")

    def test_upgrade_or_cancel_without_active_subscription_raises_value_error(self) -> None:
        # Upgrading nonexistent tenant
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_up_missing",
                "tenant_id": "missing_tenant",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 1000,
            })
        # Canceling nonexistent tenant
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_cancel_missing",
                "tenant_id": "missing_tenant",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 1001,
            })
        # Create and then cancel subscription
        self.engine.handle_webhook({
            "webhook_id": "wh_create",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 1002,
        })
        self.engine.handle_webhook({
            "webhook_id": "wh_cancel",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "starter",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 1003,
        })
        # Upgrading already-canceled subscription raises ValueError
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_up_after_cancel",
                "tenant_id": "tenant_a",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 1004,
            })
        # Canceling already-canceled subscription raises ValueError
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "wh_cancel_again",
                "tenant_id": "tenant_a",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "starter",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 1005,
            })

    def test_rollback_on_upgrade_restores_previous_subscription_and_entitlement(self) -> None:
        created = self.engine.handle_webhook({
            "webhook_id": "wh_create",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 1000,
        })
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh_upgrade_fail",
                "tenant_id": "tenant_a",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 100,
                "amount_cents": 600000,
                "timestamp": 1010,
                "fail_entitlement_sync": True,
            })
        self.assertEqual(self.engine.subscriptions["tenant_a"], created)
        self.assertEqual(
            self.engine.entitlements["tenant_a"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.invoices[0]["webhook_id"], "wh_create")
        self.assertEqual(self.engine.audit_trail[-1], {"webhook_id": "wh_upgrade_fail", "status": "ROLLED_BACK"})

    def test_rollback_on_cancel_restores_previous_subscription_and_entitlement(self) -> None:
        created = self.engine.handle_webhook({
            "webhook_id": "wh_create",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 1000,
        })
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "wh_cancel_fail",
                "tenant_id": "tenant_a",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "starter",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 1010,
                "fail_entitlement_sync": True,
            })
        self.assertEqual(self.engine.subscriptions["tenant_a"], created)
        self.assertEqual(
            self.engine.entitlements["tenant_a"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)

    def test_list_active_subscriptions_orders_enterprise_first_and_preserves_creation_order_on_upgrade(self) -> None:
        # Tenant A created 1st (STANDARD)
        self.engine.handle_webhook({
            "webhook_id": "wh_1",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 1000,
        })
        # Tenant B created 2nd (ENTERPRISE)
        self.engine.handle_webhook({
            "webhook_id": "wh_2",
            "tenant_id": "tenant_b",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent",
            "seats": 50,
            "amount_cents": 500000,
            "timestamp": 1001,
        })
        # Tenant C created 3rd (STANDARD)
        self.engine.handle_webhook({
            "webhook_id": "wh_3",
            "tenant_id": "tenant_c",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 1002,
        })
        # Before upgrade: B (ENTERPRISE), A (STANDARD), C (STANDARD)
        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["tenant_b", "tenant_a", "tenant_c"])

        # Tenant A upgrades within STANDARD: should still be before Tenant C
        self.engine.handle_webhook({
            "webhook_id": "wh_4",
            "tenant_id": "tenant_a",
            "event_type": "PLAN_UPGRADED",
            "plan": "plus",
            "seats": 20,
            "amount_cents": 20000,
            "timestamp": 1003,
        })
        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["tenant_b", "tenant_a", "tenant_c"])

        # Tenant A upgrades to ENTERPRISE: since Tenant A was created before Tenant B,
        # Tenant A should now appear before Tenant B!
        self.engine.handle_webhook({
            "webhook_id": "wh_5",
            "tenant_id": "tenant_a",
            "event_type": "PLAN_UPGRADED",
            "plan": "ent",
            "seats": 50,
            "amount_cents": 500000,
            "timestamp": 1004,
        })
        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["tenant_a", "tenant_b", "tenant_c"])


if __name__ == "__main__":
    unittest.main()
