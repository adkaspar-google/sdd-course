"""Unit tests for SubscriptionWebhookEngine."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    """Comprehensive tests for SubscriptionWebhookEngine."""

    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def _make_payload(self, **overrides):
        base = {
            "webhook_id": "wh_1",
            "tenant_id": "tenant_a",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 1000,
        }
        base.update(overrides)
        return base

    def test_create_standard_subscription(self) -> None:
        res = self.engine.handle_webhook(self._make_payload())
        self.assertEqual(res["tier"], "STANDARD")
        self.assertEqual(res["sla_hours"], 24)
        self.assertEqual(res["status"], "ACTIVE")
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.entitlements["tenant_a"], {"seats": 10, "tier": "STANDARD"})
        self.assertEqual(self.engine.audit_trail, [{"webhook_id": "wh_1", "status": "PROCESSED"}])

    def test_enterprise_tier_routing_boundaries(self) -> None:
        # Exactly 50 seats -> ENTERPRISE
        r1 = self.engine.handle_webhook(
            self._make_payload(webhook_id="wh_50_seats", tenant_id="t1", seats=50, amount_cents=100)
        )
        self.assertEqual(r1["tier"], "ENTERPRISE")
        self.assertEqual(r1["sla_hours"], 1)

        # 49 seats and 499999 cents -> STANDARD
        r2 = self.engine.handle_webhook(
            self._make_payload(webhook_id="wh_49_seats", tenant_id="t2", seats=49, amount_cents=499999)
        )
        self.assertEqual(r2["tier"], "STANDARD")
        self.assertEqual(r2["sla_hours"], 24)

        # Exactly 500000 cents -> ENTERPRISE
        r3 = self.engine.handle_webhook(
            self._make_payload(webhook_id="wh_500k_cents", tenant_id="t3", seats=1, amount_cents=500000)
        )
        self.assertEqual(r3["tier"], "ENTERPRISE")
        self.assertEqual(r3["sla_hours"], 1)

    def test_replay_safe_idempotency(self) -> None:
        payload = self._make_payload(webhook_id="wh_idem", timestamp=100)
        first = self.engine.handle_webhook(payload)
        first["plan"] = "mutated_externally"

        # Replay 10 times; should not trigger rate limits or duplicate invoices/audit
        for i in range(10):
            replay = self.engine.handle_webhook(self._make_payload(webhook_id="wh_idem", timestamp=100 + i))
            self.assertEqual(replay["plan"], "pro")
            self.assertEqual(replay["webhook_id"], "wh_idem")

        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(len(self.engine.audit_trail), 1)

    def test_validation_errors_leave_zero_state_changes(self) -> None:
        bad_payloads = [
            self._make_payload(webhook_id=""),
            self._make_payload(webhook_id="   "),
            self._make_payload(tenant_id=""),
            self._make_payload(tenant_id="  "),
            self._make_payload(event_type="UNKNOWN_EVENT"),
            self._make_payload(amount_cents=-1),
            self._make_payload(event_type="SUBSCRIPTION_CREATED", seats=0),
            self._make_payload(event_type="SUBSCRIPTION_CREATED", seats=-5),
            self._make_payload(event_type="PLAN_UPGRADED", seats=10),  # no active sub
            self._make_payload(event_type="SUBSCRIPTION_CANCELED", seats=0, amount_cents=0),  # no active sub
        ]
        for p in bad_payloads:
            with self.assertRaises(ValueError):
                self.engine.handle_webhook(p)

        self.assertEqual(self.engine.subscriptions, {})
        self.assertEqual(self.engine.invoices, [])
        self.assertEqual(self.engine.entitlements, {})
        self.assertEqual(self.engine.audit_trail, [])

    def test_cancel_and_post_cancel_validation(self) -> None:
        self.engine.handle_webhook(self._make_payload(webhook_id="wh_create", tenant_id="t1"))
        res = self.engine.handle_webhook(
            self._make_payload(
                webhook_id="wh_cancel",
                tenant_id="t1",
                event_type="SUBSCRIPTION_CANCELED",
                seats=0,
                amount_cents=0,
            )
        )
        self.assertEqual(res["status"], "CANCELED")
        self.assertEqual(self.engine.list_active_subscriptions(), [])

        # Upgrading or canceling an already-canceled tenant must raise ValueError
        with self.assertRaises(ValueError):
            self.engine.handle_webhook(
                self._make_payload(
                    webhook_id="wh_upgrade_after_cancel",
                    tenant_id="t1",
                    event_type="PLAN_UPGRADED",
                    seats=20,
                )
            )
        with self.assertRaises(ValueError):
            self.engine.handle_webhook(
                self._make_payload(
                    webhook_id="wh_cancel_again",
                    tenant_id="t1",
                    event_type="SUBSCRIPTION_CANCELED",
                    seats=0,
                    amount_cents=0,
                )
            )

    def test_transactional_rollback_on_new_and_existing_subscription(self) -> None:
        # Rollback on initial creation
        with self.assertRaisesRegex(RuntimeError, "Entitlement service unavailable"):
            self.engine.handle_webhook(
                self._make_payload(webhook_id="wh_fail_1", tenant_id="t1", fail_entitlement_sync=True)
            )
        self.assertEqual(self.engine.subscriptions, {})
        self.assertEqual(self.engine.invoices, [])
        self.assertEqual(self.engine.entitlements, {})
        self.assertEqual(self.engine.audit_trail, [{"webhook_id": "wh_fail_1", "status": "ROLLED_BACK"}])

        # Create valid subscription for t1
        self.engine.handle_webhook(
            self._make_payload(
                webhook_id="wh_ok_1",
                tenant_id="t1",
                plan="basic",
                seats=10,
                amount_cents=1000,
            )
        )
        # Attempt upgrade that fails entitlement sync
        with self.assertRaisesRegex(RuntimeError, "Entitlement service unavailable"):
            self.engine.handle_webhook(
                self._make_payload(
                    webhook_id="wh_fail_upgrade",
                    tenant_id="t1",
                    event_type="PLAN_UPGRADED",
                    plan="enterprise",
                    seats=100,
                    amount_cents=900000,
                    fail_entitlement_sync=True,
                )
            )
        # Previous subscription, invoice, and entitlement must remain intact
        self.assertEqual(self.engine.subscriptions["t1"]["plan"], "basic")
        self.assertEqual(self.engine.subscriptions["t1"]["seats"], 10)
        self.assertEqual(self.engine.subscriptions["t1"]["tier"], "STANDARD")
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.entitlements["t1"], {"seats": 10, "tier": "STANDARD"})
        self.assertEqual(
            self.engine.audit_trail,
            [
                {"webhook_id": "wh_fail_1", "status": "ROLLED_BACK"},
                {"webhook_id": "wh_ok_1", "status": "PROCESSED"},
                {"webhook_id": "wh_fail_upgrade", "status": "ROLLED_BACK"},
            ],
        )

    def test_sliding_window_rate_limit(self) -> None:
        # 1st at t=100 (create)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w1", tenant_id="t1", event_type="SUBSCRIPTION_CREATED", timestamp=100)
        )
        # 2nd at t=120 (upgrade)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w2", tenant_id="t1", event_type="PLAN_UPGRADED", seats=15, timestamp=120)
        )
        # 3rd at t=140 (upgrade)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w3", tenant_id="t1", event_type="PLAN_UPGRADED", seats=20, timestamp=140)
        )
        # Failed entitlement sync at t=150 should NOT count toward rate limit
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook(
                self._make_payload(
                    webhook_id="w_fail",
                    tenant_id="t1",
                    event_type="PLAN_UPGRADED",
                    seats=25,
                    timestamp=150,
                    fail_entitlement_sync=True,
                )
            )
        # 4th successful at t=160 (inclusive boundary: 160 - 100 == 60)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w4", tenant_id="t1", event_type="PLAN_UPGRADED", seats=30, timestamp=160)
        )
        # 5th at t=160 must fail with Rate limit exceeded and zero state changes
        with self.assertRaisesRegex(ValueError, "Rate limit exceeded"):
            self.engine.handle_webhook(
                self._make_payload(webhook_id="w5", tenant_id="t1", event_type="PLAN_UPGRADED", seats=40, timestamp=160)
            )
        self.assertEqual(self.engine.subscriptions["t1"]["seats"], 30)
        self.assertEqual(len(self.engine.invoices), 4)

        # At t=161, t=100 is outside the 60s window (161 - 100 = 61 > 60), so w5 succeeds!
        res = self.engine.handle_webhook(
            self._make_payload(webhook_id="w5", tenant_id="t1", event_type="PLAN_UPGRADED", seats=40, timestamp=161)
        )
        self.assertEqual(res["seats"], 40)

    def test_list_active_subscriptions_ordering_and_upgrade_tie_breaking(self) -> None:
        # t1 created first (STANDARD)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w1", tenant_id="t1", seats=10, amount_cents=1000, timestamp=10)
        )
        # t2 created second (ENTERPRISE)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w2", tenant_id="t2", seats=50, amount_cents=1000, timestamp=20)
        )
        # t3 created third (STANDARD)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w3", tenant_id="t3", seats=5, amount_cents=1000, timestamp=30)
        )
        # t4 created fourth (ENTERPRISE)
        self.engine.handle_webhook(
            self._make_payload(webhook_id="w4", tenant_id="t4", seats=10, amount_cents=500000, timestamp=40)
        )

        active = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active], ["t2", "t4", "t1", "t3"])

        # Now t1 upgrades to ENTERPRISE. Its original creation order was 1st (before t2 and t4)!
        self.engine.handle_webhook(
            self._make_payload(
                webhook_id="w5",
                tenant_id="t1",
                event_type="PLAN_UPGRADED",
                seats=60,
                amount_cents=1000,
                timestamp=50,
            )
        )
        active_after_upgrade = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active_after_upgrade], ["t1", "t2", "t4", "t3"])


if __name__ == "__main__":
    unittest.main()
