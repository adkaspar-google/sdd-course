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
"""Comprehensive boundary and equivalence-class tests for SubscriptionWebhookEngine."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):
    """Tests all 7 requirements and contrastive boundaries for SubscriptionWebhookEngine."""

    def setUp(self) -> None:
        self.engine = SubscriptionWebhookEngine()

    def test_out_of_scope_legacy_todos_not_implemented(self) -> None:
        """Unrequested # TODO helper methods must not be implemented."""
        self.assertFalse(hasattr(self.engine, "send_welcome_gift"))
        self.assertFalse(hasattr(self.engine, "dump_debug_log"))

    def test_enterprise_tier_exact_boundaries(self) -> None:
        """Seats >= 50 or amount_cents >= 500000 routes to ENTERPRISE (sla_hours=1), else STANDARD (24)."""
        # Exact boundary: seats == 50, amount_cents < 500000 -> ENTERPRISE
        r1 = self.engine.handle_webhook({
            "webhook_id": "w1",
            "tenant_id": "t_seats_50",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 50,
            "amount_cents": 1000,
            "timestamp": 100,
        })
        self.assertEqual(r1["tier"], "ENTERPRISE")
        self.assertEqual(r1["sla_hours"], 1)

        # Exact boundary: seats == 49, amount_cents == 500000 -> ENTERPRISE
        r2 = self.engine.handle_webhook({
            "webhook_id": "w2",
            "tenant_id": "t_amount_500k",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "pro",
            "seats": 49,
            "amount_cents": 500000,
            "timestamp": 100,
        })
        self.assertEqual(r2["tier"], "ENTERPRISE")
        self.assertEqual(r2["sla_hours"], 1)

        # Below boundary: seats == 49, amount_cents == 499999 -> STANDARD
        r3 = self.engine.handle_webhook({
            "webhook_id": "w3",
            "tenant_id": "t_standard",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 49,
            "amount_cents": 499999,
            "timestamp": 100,
        })
        self.assertEqual(r3["tier"], "STANDARD")
        self.assertEqual(r3["sla_hours"], 24)

    def test_replay_safe_idempotency(self) -> None:
        """Duplicate webhook_id returns a copy of original result with zero side effects or rate-limit count."""
        payload = {
            "webhook_id": "wh_idem_1",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 10,
            "amount_cents": 10000,
            "timestamp": 10,
        }
        first = self.engine.handle_webhook(payload)
        first["plan"] = "MUTATED_BY_CALLER"

        # Replay with modified fields in payload - should return original result copy
        replay = self.engine.handle_webhook({
            "webhook_id": "wh_idem_1",
            "tenant_id": "t1",
            "event_type": "PLAN_UPGRADED",
            "plan": "enterprise",
            "seats": 100,
            "amount_cents": 900000,
            "timestamp": 15,
        })
        self.assertEqual(replay["plan"], "basic")
        self.assertEqual(replay["seats"], 10)
        self.assertEqual(len(self.engine.invoices), 1)
        self.assertEqual(len(self.engine.audit_trail), 1)
        self.assertEqual(self.engine.entitlements["t1"], {"seats": 10, "tier": "STANDARD"})

        # Replaying 10 times does not consume rate limit quota
        for _ in range(10):
            self.engine.handle_webhook(payload)

        # Should still be able to perform 3 more state-changing webhooks in the same 60s window
        for i in range(2, 5):
            self.engine.handle_webhook({
                "webhook_id": f"wh_{i}",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": f"plan_{i}",
                "seats": 10 + i,
                "amount_cents": 10000,
                "timestamp": 10 + i,
            })
        self.assertEqual(len(self.engine.invoices), 4)

    def test_input_validation_and_state_transition_guards(self) -> None:
        """Invalid payloads and invalid lifecycle transitions raise ValueError with zero state changes."""
        invalid_payloads = [
            # Unknown event_type
            {
                "webhook_id": "v1",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_PAUSED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 100,
                "timestamp": 10,
            },
            # Blank webhook_id
            {
                "webhook_id": "   ",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 100,
                "timestamp": 10,
            },
            # None webhook_id
            {
                "webhook_id": None,
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 100,
                "timestamp": 10,
            },
            # Blank tenant_id
            {
                "webhook_id": "v2",
                "tenant_id": "",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": 100,
                "timestamp": 10,
            },
            # Negative amount_cents
            {
                "webhook_id": "v3",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 5,
                "amount_cents": -1,
                "timestamp": 10,
            },
            # Zero seats on SUBSCRIPTION_CREATED
            {
                "webhook_id": "v4",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 100,
                "timestamp": 10,
            },
            # Negative seats on SUBSCRIPTION_CREATED
            {
                "webhook_id": "v5",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "pro",
                "seats": -3,
                "amount_cents": 100,
                "timestamp": 10,
            },
            # Upgrade without existing active subscription
            {
                "webhook_id": "v6",
                "tenant_id": "nonexistent",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 1000,
                "timestamp": 10,
            },
            # Cancel without existing active subscription
            {
                "webhook_id": "v7",
                "tenant_id": "nonexistent",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 10,
            },
        ]

        for bad in invalid_payloads:
            with self.assertRaises(ValueError):
                self.engine.handle_webhook(bad)

        self.assertEqual(self.engine.subscriptions, {})
        self.assertEqual(self.engine.invoices, [])
        self.assertEqual(self.engine.entitlements, {})
        self.assertEqual(self.engine.audit_trail, [])

        # Now create a valid subscription, cancel it with seats=0 and amount_cents=0, then test upgrading/canceling again
        self.engine.handle_webhook({
            "webhook_id": "valid_create",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 5,
            "amount_cents": 500,
            "timestamp": 20,
        })
        # Zero seats on PLAN_UPGRADED must fail
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "bad_upgrade_seats",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 0,
                "amount_cents": 1000,
                "timestamp": 25,
            })

        # Cancel with seats=0, amount_cents=0 must succeed
        canceled = self.engine.handle_webhook({
            "webhook_id": "valid_cancel",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "basic",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 30,
        })
        self.assertEqual(canceled["status"], "CANCELED")

        # Upgrading or canceling an already-canceled subscription must raise ValueError
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "upgrade_after_cancel",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "pro",
                "seats": 10,
                "amount_cents": 1000,
                "timestamp": 35,
            })
        with self.assertRaises(ValueError):
            self.engine.handle_webhook({
                "webhook_id": "cancel_after_cancel",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "basic",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 36,
            })

    def test_transactional_rollback_preserves_prior_state(self) -> None:
        """fail_entitlement_sync=True rolls back subscriptions, invoices, and entitlements while auditing ROLLED_BACK."""
        # 1. Rollback on initial creation
        with self.assertRaisesRegex(RuntimeError, "Entitlement service unavailable"):
            self.engine.handle_webhook({
                "webhook_id": "wh_fail_create",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CREATED",
                "plan": "starter",
                "seats": 10,
                "amount_cents": 1000,
                "timestamp": 10,
                "fail_entitlement_sync": True,
            })
        self.assertEqual(self.engine.subscriptions, {})
        self.assertEqual(self.engine.invoices, [])
        self.assertEqual(self.engine.entitlements, {})
        self.assertEqual(
            self.engine.audit_trail,
            [{"webhook_id": "wh_fail_create", "status": "ROLLED_BACK"}],
        )

        # 2. Succeed on creation
        self.engine.handle_webhook({
            "webhook_id": "wh_ok_create",
            "tenant_id": "t1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "starter",
            "seats": 10,
            "amount_cents": 1000,
            "timestamp": 20,
        })
        sub_snapshot = dict(self.engine.subscriptions["t1"])
        inv_snapshot = list(self.engine.invoices)
        ent_snapshot = dict(self.engine.entitlements["t1"])

        # 3. Rollback on in-place PLAN_UPGRADED
        with self.assertRaisesRegex(RuntimeError, "Entitlement service unavailable"):
            self.engine.handle_webhook({
                "webhook_id": "wh_fail_upgrade",
                "tenant_id": "t1",
                "event_type": "PLAN_UPGRADED",
                "plan": "enterprise",
                "seats": 100,
                "amount_cents": 800000,
                "timestamp": 30,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t1"], sub_snapshot)
        self.assertEqual(self.engine.invoices, inv_snapshot)
        self.assertEqual(self.engine.entitlements["t1"], ent_snapshot)
        self.assertEqual(
            self.engine.audit_trail[-1],
            {"webhook_id": "wh_fail_upgrade", "status": "ROLLED_BACK"},
        )

        # 4. Rollback on SUBSCRIPTION_CANCELED
        with self.assertRaisesRegex(RuntimeError, "Entitlement service unavailable"):
            self.engine.handle_webhook({
                "webhook_id": "wh_fail_cancel",
                "tenant_id": "t1",
                "event_type": "SUBSCRIPTION_CANCELED",
                "plan": "starter",
                "seats": 0,
                "amount_cents": 0,
                "timestamp": 40,
                "fail_entitlement_sync": True,
            })

        self.assertEqual(self.engine.subscriptions["t1"], sub_snapshot)
        self.assertEqual(self.engine.invoices, inv_snapshot)
        self.assertEqual(self.engine.entitlements["t1"], ent_snapshot)
        self.assertEqual(
            self.engine.audit_trail[-1],
            {"webhook_id": "wh_fail_cancel", "status": "ROLLED_BACK"},
        )

    def test_sliding_window_rate_limit_boundaries(self) -> None:
        """At most 4 successful webhooks in inclusive 60s window (0 <= current - prev <= 60)."""
        self.engine.handle_webhook({
            "webhook_id": "rl_1",
            "tenant_id": "t_rate",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "p1",
            "seats": 5,
            "amount_cents": 500,
            "timestamp": 100,
        })
        for idx, ts in enumerate([110, 130, 150], start=2):
            self.engine.handle_webhook({
                "webhook_id": f"rl_{idx}",
                "tenant_id": "t_rate",
                "event_type": "PLAN_UPGRADED",
                "plan": f"p{idx}",
                "seats": 5 + idx,
                "amount_cents": 500 + idx * 100,
                "timestamp": ts,
            })

        # 5th webhook at exact boundary timestamp=160 (160 - 100 == 60 <= 60) must fail
        with self.assertRaisesRegex(ValueError, "Rate limit exceeded"):
            self.engine.handle_webhook({
                "webhook_id": "rl_5_blocked",
                "tenant_id": "t_rate",
                "event_type": "PLAN_UPGRADED",
                "plan": "p5",
                "seats": 20,
                "amount_cents": 2000,
                "timestamp": 160,
            })
        self.assertEqual(self.engine.subscriptions["t_rate"]["plan"], "p4")
        self.assertEqual(len(self.engine.invoices), 4)

        # At timestamp=161 (161 - 100 == 61 > 60), oldest webhook aged out -> only 3 in [101, 161] -> succeeds
        res = self.engine.handle_webhook({
            "webhook_id": "rl_5_allowed",
            "tenant_id": "t_rate",
            "event_type": "PLAN_UPGRADED",
            "plan": "p5",
            "seats": 20,
            "amount_cents": 2000,
            "timestamp": 161,
        })
        self.assertEqual(res["plan"], "p5")
        self.assertEqual(len(self.engine.invoices), 5)

    def test_list_active_subscriptions_tier_and_creation_order(self) -> None:
        """Orders ENTERPRISE before STANDARD, breaking ties by original subscription creation order."""
        # Create t_std_1 (order 1, STANDARD)
        self.engine.handle_webhook({
            "webhook_id": "o1",
            "tenant_id": "t_std_1",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 10,
            "amount_cents": 1000,
            "timestamp": 10,
        })
        # Create t_ent_2 (order 2, ENTERPRISE)
        self.engine.handle_webhook({
            "webhook_id": "o2",
            "tenant_id": "t_ent_2",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent",
            "seats": 60,
            "amount_cents": 10000,
            "timestamp": 20,
        })
        # Create t_std_3 (order 3, STANDARD)
        self.engine.handle_webhook({
            "webhook_id": "o3",
            "tenant_id": "t_std_3",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "basic",
            "seats": 5,
            "amount_cents": 500,
            "timestamp": 30,
        })
        # Create t_ent_4 (order 4, ENTERPRISE)
        self.engine.handle_webhook({
            "webhook_id": "o4",
            "tenant_id": "t_ent_4",
            "event_type": "SUBSCRIPTION_CREATED",
            "plan": "ent",
            "seats": 10,
            "amount_cents": 500000,
            "timestamp": 40,
        })

        active = [s["tenant_id"] for s in self.engine.list_active_subscriptions()]
        self.assertEqual(active, ["t_ent_2", "t_ent_4", "t_std_1", "t_std_3"])

        # Now upgrade t_std_1 (original creation order 1) to ENTERPRISE!
        # Because its original creation order (1) is earlier than t_ent_2 (2) and t_ent_4 (4),
        # t_std_1 must now appear FIRST among ENTERPRISE subscriptions!
        self.engine.handle_webhook({
            "webhook_id": "o5_upgrade",
            "tenant_id": "t_std_1",
            "event_type": "PLAN_UPGRADED",
            "plan": "ent_plus",
            "seats": 50,
            "amount_cents": 20000,
            "timestamp": 50,
        })

        active_after_upgrade = [s["tenant_id"] for s in self.engine.list_active_subscriptions()]
        self.assertEqual(active_after_upgrade, ["t_std_1", "t_ent_2", "t_ent_4", "t_std_3"])

        # Cancel t_ent_2 -> excluded from active subscriptions
        self.engine.handle_webhook({
            "webhook_id": "o6_cancel",
            "tenant_id": "t_ent_2",
            "event_type": "SUBSCRIPTION_CANCELED",
            "plan": "ent",
            "seats": 0,
            "amount_cents": 0,
            "timestamp": 60,
        })
        active_after_cancel = [s["tenant_id"] for s in self.engine.list_active_subscriptions()]
        self.assertEqual(active_after_cancel, ["t_std_1", "t_ent_4", "t_std_3"])


if __name__ == "__main__":
    unittest.main()
