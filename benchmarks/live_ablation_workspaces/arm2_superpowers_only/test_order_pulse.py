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
"""Unit tests for OrderPulse workflow engine (Sprints 1-3)."""

import unittest
from order_pulse import (
    DownstreamServiceError,
    OrderPulseEngine,
    RateLimitExceededError,
)


class TestOrderPulseEngine(unittest.TestCase):
    """Verifies idempotency, rollback, VIP routing, rate limiting, and priority sorting."""

    def setUp(self) -> None:
        self.engine = OrderPulseEngine(initial_stock={"SKU-1": 20, "SKU-2": 10})

    def test_standard_and_vip_boundary_routing(self) -> None:
        std_order = self.engine.process_order(
            {
                "event_id": "evt-1",
                "customer_id": "cust-1",
                "sku": "SKU-1",
                "qty": 2,
                "total_cents": 99999,
                "priority": "LOW",
                "timestamp": 10,
            }
        )
        self.assertEqual(std_order["channel"], "#orders")
        self.assertEqual(std_order["priority"], "LOW")

        vip_order = self.engine.process_order(
            {
                "event_id": "evt-2",
                "customer_id": "cust-1",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 100000,
                "priority": "LOW",
                "timestamp": 20,
            }
        )
        self.assertEqual(vip_order["channel"], "#vip-orders")
        self.assertEqual(vip_order["priority"], "HIGH")

    def test_idempotent_duplicate_event_id(self) -> None:
        event = {
            "event_id": "evt-dup",
            "customer_id": "cust-2",
            "sku": "SKU-1",
            "qty": 3,
            "total_cents": 5000,
            "timestamp": 100,
        }
        first = self.engine.process_order(event)
        second = self.engine.process_order(event)
        self.assertEqual(first, second)
        self.assertEqual(self.engine.stock["SKU-1"], 17)
        self.assertEqual(len(self.engine.charges), 1)
        self.assertEqual(len(self.engine.slack_messages), 1)
        self.assertEqual(len(self.engine.orders), 1)

    def test_rollback_on_billing_and_slack_failures(self) -> None:
        with self.assertRaises(DownstreamServiceError):
            self.engine.process_order(
                {
                    "event_id": "evt-bill-fail",
                    "customer_id": "cust-3",
                    "sku": "SKU-1",
                    "qty": 5,
                    "total_cents": 25000,
                    "timestamp": 50,
                    "simulate_billing_failure": True,
                }
            )
        self.assertEqual(self.engine.stock["SKU-1"], 20)
        self.assertEqual(len(self.engine.charges), 0)
        self.assertEqual(len(self.engine.orders), 0)

        with self.assertRaises(DownstreamServiceError):
            self.engine.process_order(
                {
                    "event_id": "evt-slack-fail",
                    "customer_id": "cust-3",
                    "sku": "SKU-1",
                    "qty": 5,
                    "total_cents": 25000,
                    "timestamp": 55,
                    "simulate_slack_failure": True,
                }
            )
        self.assertEqual(self.engine.stock["SKU-1"], 20)
        self.assertEqual(len(self.engine.charges), 0)
        self.assertEqual(len(self.engine.slack_messages), 0)
        self.assertEqual(len(self.engine.orders), 0)

    def test_sliding_window_rate_limit_three_orders_per_60s(self) -> None:
        for i, ts in enumerate([100, 120, 160], start=1):
            self.engine.process_order(
                {
                    "event_id": f"evt-rl-{i}",
                    "customer_id": "cust-rl",
                    "sku": "SKU-1",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": ts,
                }
            )
        with self.assertRaises(RateLimitExceededError):
            self.engine.process_order(
                {
                    "event_id": "evt-rl-4",
                    "customer_id": "cust-rl",
                    "sku": "SKU-1",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": 160,
                }
            )
        # After window expires (t=161 is >60s after t=100), order succeeds
        fourth = self.engine.process_order(
            {
                "event_id": "evt-rl-5",
                "customer_id": "cust-rl",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 1000,
                "timestamp": 161,
            }
        )
        self.assertEqual(fourth["status"], "CONFIRMED")

    def test_priority_sorting_in_list_pending_fulfillments(self) -> None:
        self.engine.process_order(
            {
                "event_id": "evt-low",
                "customer_id": "c1",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 1000,
                "priority": "LOW",
                "timestamp": 10,
            }
        )
        self.engine.process_order(
            {
                "event_id": "evt-med",
                "customer_id": "c2",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 2000,
                "priority": "MEDIUM",
                "timestamp": 20,
            }
        )
        self.engine.process_order(
            {
                "event_id": "evt-high",
                "customer_id": "c3",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 100000,
                "priority": "LOW",
                "timestamp": 30,
            }
        )
        pending = self.engine.list_pending_fulfillments()
        self.assertEqual(
            [o["event_id"] for o in pending],
            ["evt-high", "evt-med", "evt-low"],
        )


if __name__ == "__main__":
    unittest.main()
