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
"""Smoke tests for OrderPulseEngine (Vibe Coding session)."""

import unittest
from order_pulse import DownstreamServiceError, OrderPulseEngine, RateLimitExceededError


class TestOrderPulseSmoke(unittest.TestCase):
    def test_idempotency_and_vip_routing(self) -> None:
        engine = OrderPulseEngine({"SKU-1": 10})
        evt = {
            "event_id": "evt-1",
            "customer_id": "cust-1",
            "sku": "SKU-1",
            "qty": 2,
            "total_cents": 150000,
            "timestamp": 100,
        }
        res1 = engine.process_order(evt)
        res2 = engine.process_order(evt)
        self.assertEqual(res1["event_id"], "evt-1")
        self.assertEqual(res1["channel"], "#vip-orders")
        self.assertEqual(res1["priority"], "HIGH")
        self.assertEqual(len(engine.charges), 1)
        self.assertEqual(engine.stock["SKU-1"], 8)
        self.assertEqual(res1, res2)

    def test_rollback_on_failures(self) -> None:
        engine = OrderPulseEngine({"SKU-1": 5})
        with self.assertRaises(DownstreamServiceError):
            engine.process_order(
                {
                    "event_id": "evt-fail-1",
                    "customer_id": "cust-1",
                    "sku": "SKU-1",
                    "qty": 2,
                    "total_cents": 5000,
                    "simulate_billing_failure": True,
                }
            )
        self.assertEqual(engine.stock["SKU-1"], 5)
        self.assertEqual(len(engine.charges), 0)

        with self.assertRaises(DownstreamServiceError):
            engine.process_order(
                {
                    "event_id": "evt-fail-2",
                    "customer_id": "cust-1",
                    "sku": "SKU-1",
                    "qty": 2,
                    "total_cents": 5000,
                    "simulate_slack_failure": True,
                }
            )
        self.assertEqual(engine.stock["SKU-1"], 5)
        self.assertEqual(len(engine.charges), 0)

    def test_rate_limit_and_priority_sorting(self) -> None:
        engine = OrderPulseEngine({"SKU-1": 20})
        for i, prio in enumerate(["LOW", "HIGH", "MEDIUM"]):
            engine.process_order(
                {
                    "event_id": f"evt-{i}",
                    "customer_id": "cust-rate",
                    "sku": "SKU-1",
                    "qty": 1,
                    "total_cents": 1000,
                    "priority": prio,
                    "timestamp": 10 + i * 10,
                }
            )
        with self.assertRaises(RateLimitExceededError):
            engine.process_order(
                {
                    "event_id": "evt-4",
                    "customer_id": "cust-rate",
                    "sku": "SKU-1",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": 45,
                }
            )
        pending = engine.list_pending_fulfillments()
        self.assertEqual([o["priority"] for o in pending], ["HIGH", "MEDIUM", "LOW"])

    def test_promo_and_csv_helpers(self) -> None:
        engine = OrderPulseEngine({"SKU-1": 5})
        self.assertEqual(engine.apply_promo_discount(10000, 15.0), 8500)
        engine.process_order(
            {
                "event_id": "evt-csv",
                "customer_id": "cust-csv",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 8500,
                "timestamp": 10,
            }
        )
        self.assertIn("evt-csv", engine.export_csv())


if __name__ == "__main__":
    unittest.main()
