# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for SubscriptionWebhookEngine."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def test_tier_boundary_seats_and_amount(self) -> None:
        # 49 seats and 499999 cents -> STANDARD (sla_hours=24)
        res_std = self.engine.handle_webhook({
            "webhook_id": "wh_std",
            "tenant_id": "t_std",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 49,
            "amount_cents": 499999,
            "timestamp": 100,
        })
        self.assertEqual(res_std["tier"], "STANDARD")
        self.assertEqual(res_std["sla_hours"], 24)

        # Exactly 50 seats -> ENTERPRISE (sla_hours=1)
        res_ent_seats = self.engine.handle_webhook({
            "webhook_id": "wh_ent_seats",
            "tenant_id": "t_ent_seats",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "enterprise_seats",
            "seats": 50,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        self.assertEqual(res_ent_seats["tier"], "ENTERPRISE")
        self.assertEqual(res_ent_seats["sla_hours"], 1)

        # Exactly 500000 cents ($5,000) -> ENTERPRISE (sla_hours=1)
        res_ent_amt = self.engine.handle_webhook({
            "webhook_id": "wh_ent_amt",
            "tenant_id": "t_ent_amt",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "enterprise_amt",
            "seats": 10,
            "amount_cents": 500000,
            "timestamp": 100,
        })
        self.assertEqual(res_ent_amt["tier"], "ENTERPRISE")
        self.assertEqual(res_ent_amt["sla_hours"], 1)

    def test_rate_limit_inclusive_60_second_window_and_successful_only(self) -> None:
        # 1st successful webhook at t=100
        self.engine.handle_webhook({
            "webhook_id": "w1",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 100,
        })
        # Failed webhook at t=105 should NOT count toward rate limit
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "w_fail",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 105,
                "fail_entitlement_sync": True,
            })
        # 2nd, 3rd, 4th successful webhooks at t=110, 120, 130
        for idx, ts in enumerate((110, 120, 130), start=2):
            self.engine.handle_webhook({
                "webhook_id": f"w{idx}",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": f"plan_{idx}",
                "seats": 5 + idx,
                "amount_cents": 5000 * idx,
                "timestamp": ts,
            })

        # At t=160 (160 - 100 == 60, within inclusive 60s window), 5th webhook is rate-limited
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "w5_blocked",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "blocked",
                "seats": 20,
                "amount_cents": 20000,
                "timestamp": 160,
            })

        # At t=161 (161 - 100 == 61, outside 60s window for w1), webhook succeeds
        res = self.engine.handle_webhook({
            "webhook_id": "w5_allowed",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "allowed",
            "seats": 20,
            "amount_cents": 20000,
            "timestamp": 161,
        })
        self.assertEqual(res["plan"], "allowed")

    def test_upgrade_or_cancel_without_active_subscription_raises(self) -> None:
        # Unknown tenant
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "w_up_missing",
                "tenant_id": "no_sub",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 100,
            })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "w_cancel_missing",
                "tenant_id": "no_sub",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 100,
            })

        # Create and then cancel a subscription
        self.engine.handle_webhook({
            "webhook_id": "w_create",
            "tenant_id": "t_canceled",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 5,
            "amount_cents": 5000,
            "timestamp": 100,
        })
        self.engine.handle_webhook({
            "webhook_id": "w_cancel_1",
            "tenant_id": "t_canceled",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "starter",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 110,
        })

        # Upgrading or canceling an already-canceled subscription must raise ValueError
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "w_up_after_cancel",
                "tenant_id": "t_canceled",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 10000,
                "timestamp": 120,
            })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "w_cancel_2",
                "tenant_id": "t_canceled",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "starter",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 125,
            })

    def test_rollback_restores_previous_subscription_and_entitlement(self) -> None:
        created = self.engine.handle_webhook({
            "webhook_id": "w_init",
            "tenant_id": "t_rb",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })

        # Failed upgrade rolls back and preserves starter subscription & entitlement
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "w_up_fail",
                "tenant_id": "t_rb",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 60,
                "amount_cents": 600000,
                "timestamp": 110,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t_rb"], created)
        self.assertEqual(
            self.engine.entitlements["t_rb"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.audit_trail[-1], {"webhook_id": "w_up_fail", "status": "ROLLED_BACK"})

        # Failed cancel rolls back and preserves starter subscription & entitlement
        with self.assertRaises(RuntimeError):
            self.engine.handle_webhook({
                "webhook_id": "w_cancel_fail",
                "tenant_id": "t_rb",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "starter",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 120,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t_rb"], created)
        self.assertEqual(
            self.engine.entitlements["t_rb"],
            {"plan": "starter", "seats": 10, "tier": "STANDARD"},
        )
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(self.engine.audit_trail[-1], {"webhook_id": "w_cancel_fail", "status": "ROLLED_BACK"})

    def test_list_active_subscriptions_preserves_creation_order_on_upgrade(self) -> None:
        # t1 created first (STANDARD, seq=1)
        self.engine.handle_webhook({
            "webhook_id": "w_t1_create",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "std_1",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 100,
        })
        # t2 created second (ENTERPRISE, seq=2)
        self.engine.handle_webhook({
            "webhook_id": "w_t2_create",
            "tenant_id": "t2",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent_2",
            "seats": 50,
            "amount_cents": 200000,
            "timestamp": 110,
        })
        # t3 created third (STANDARD, seq=3)
        self.engine.handle_webhook({
            "webhook_id": "w_t3_create",
            "tenant_id": "t3",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "std_3",
            "seats": 15,
            "amount_cents": 15000,
            "timestamp": 120,
        })

        # Upgrade t1 within STANDARD -> should still precede t3
        self.engine.handle_webhook({
            "webhook_id": "w_t1_up_std",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "std_1_plus",
            "seats": 25,
            "amount_cents": 25000,
            "timestamp": 130,
        })
        active_1 = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active_1], ["t2", "t1", "t3"])

        # Upgrade t1 to ENTERPRISE -> should precede t2 because t1 was created first (seq=1 < seq=2)
        self.engine.handle_webhook({
            "webhook_id": "w_t1_up_ent",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "ent_1",
            "seats": 50,
            "amount_cents": 500000,
            "timestamp": 140,
        })
        active_2 = self.engine.list_active_subscriptions()
        self.assertEqual([s["tenant_id"] for s in active_2], ["t1", "t2", "t3"])


if __name__ == "__main__":
    unittest.main()
