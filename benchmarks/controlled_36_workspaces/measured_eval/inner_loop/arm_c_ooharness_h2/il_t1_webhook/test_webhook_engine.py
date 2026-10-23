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
"""Unit tests for SubscriptionWebhookEngine using OO-Harness + Harness^2 boundary probes."""

import unittest
from webhook_engine import SubscriptionWebhookEngine


class TestSubscriptionWebhookEngine(unittest.TestCase):

  def setUp(self) -> None:
    self.engine = SubscriptionWebhookEngine()

  def test_enterprise_tier_exact_boundaries(self) -> None:
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
    self.assertEqual(len(self.engine.invoices), 1)
    self.assertEqual(len(self.engine.audit_trail), 1)

  def test_sliding_window_rate_limit_boundaries(self) -> None:
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

  def test_transactional_rollback_and_ordering(self) -> None:
    self.engine.handle_webhook({
        "webhook_id": "wh_ok",
        "tenant_id": "t1",
        "event_type": "SUBSCRIPTION_CREATED",
        "plan": "starter",
        "seats": 10,
        "amount_cents": 1000,
        "timestamp": 20,
    })
    with self.assertRaises(RuntimeError):
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
    self.assertEqual(self.engine.subscriptions["t1"]["plan"], "starter")
    self.assertEqual(len(self.engine.invoices), 1)


if __name__ == "__main__":
  unittest.main()
