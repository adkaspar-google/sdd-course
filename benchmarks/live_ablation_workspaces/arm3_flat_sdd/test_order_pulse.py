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
"""Unit tests for Arm 3 Flat Outer-Loop SDD OrderPulseEngine."""

import unittest

from order_pulse import (
    DownstreamServiceError,
    OrderPulseEngine,
    RateLimitExceededError,
)


class OrderPulseEngineTest(unittest.TestCase):
    """Verifies REQ-0001 through REQ-0005 for OrderPulseEngine."""

    def test_req_0001_idempotent_replay(self) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-1": 10})
        event = {
            "event_id": "evt-100",
            "customer_id": "cust-1",
            "sku": "SKU-1",
            "qty": 2,
            "total_cents": 2500,
            "timestamp": 1000,
        }
        first = engine.process_order(event)
        second = engine.process_order(event)

        self.assertEqual(first, second)
        self.assertEqual(engine.stock["SKU-1"], 8)
        self.assertEqual(len(engine.orders), 1)
        self.assertEqual(len(engine.charges), 1)
        self.assertEqual(len(engine.slack_messages), 1)
        self.assertEqual(len(engine.audit_log), 1)

    def test_req_0002_rollback_on_billing_and_slack_failure(self) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-1": 5})

        with self.assertRaises(DownstreamServiceError):
            engine.process_order(
                {
                    "event_id": "evt-bill-fail",
                    "customer_id": "cust-1",
                    "sku": "SKU-1",
                    "qty": 2,
                    "total_cents": 4000,
                    "timestamp": 1010,
                    "simulate_billing_failure": True,
                }
            )
        self.assertEqual(engine.stock["SKU-1"], 5)
        self.assertEqual(len(engine.charges), 0)
        self.assertIn(
            {"event_id": "evt-bill-fail", "status": "ROLLED_BACK"},
            engine.audit_log,
        )

        with self.assertRaises(DownstreamServiceError):
            engine.process_order(
                {
                    "event_id": "evt-slack-fail",
                    "customer_id": "cust-1",
                    "sku": "SKU-1",
                    "qty": 3,
                    "total_cents": 6000,
                    "timestamp": 1020,
                    "simulate_slack_failure": True,
                }
            )
        self.assertEqual(engine.stock["SKU-1"], 5)
        self.assertEqual(len(engine.charges), 0)
        self.assertEqual(len(engine.orders), 0)
        self.assertIn(
            {"event_id": "evt-slack-fail", "status": "ROLLED_BACK"},
            engine.audit_log,
        )

    def test_req_0003_vip_routing_and_priority_escalation(self) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-VIP": 5})
        record = engine.process_order(
            {
                "event_id": "evt-vip-boundary",
                "customer_id": "cust-vip",
                "sku": "SKU-VIP",
                "qty": 1,
                "total_cents": 100000,
                "priority": "LOW",
                "timestamp": 2000,
            }
        )
        self.assertEqual(record["channel"], "#vip-orders")
        self.assertEqual(record["priority"], "HIGH")
        self.assertEqual(engine.slack_messages[-1]["channel"], "#vip-orders")
        self.assertEqual(engine.slack_messages[-1]["priority"], "HIGH")

    def test_req_0004_sliding_window_rate_limit(self) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-1": 20})
        for idx, ts in enumerate([100, 120, 140]):
            engine.process_order(
                {
                    "event_id": f"evt-rl-{idx}",
                    "customer_id": "cust-burst",
                    "sku": "SKU-1",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": ts,
                }
            )

        with self.assertRaises(RateLimitExceededError):
            engine.process_order(
                {
                    "event_id": "evt-rl-blocked",
                    "customer_id": "cust-burst",
                    "sku": "SKU-1",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": 150,
                }
            )

        # After 60s window advances past first order (160 - 100 == 60, not < 60)
        allowed = engine.process_order(
            {
                "event_id": "evt-rl-allowed",
                "customer_id": "cust-burst",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 1000,
                "timestamp": 160,
            }
        )
        self.assertEqual(allowed["status"], "CONFIRMED")

    def test_req_0005_pending_fulfillments_priority_fifo_and_scope_guard(self) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-1": 20})
        engine.process_order(
            {
                "event_id": "evt-low-1",
                "customer_id": "c1",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 1000,
                "priority": "LOW",
                "timestamp": 10,
            }
        )
        engine.process_order(
            {
                "event_id": "evt-med-1",
                "customer_id": "c2",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 2000,
                "priority": "MEDIUM",
                "timestamp": 20,
            }
        )
        engine.process_order(
            {
                "event_id": "evt-high-1",
                "customer_id": "c3",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 100000,
                "priority": "LOW",
                "timestamp": 30,
            }
        )
        engine.process_order(
            {
                "event_id": "evt-med-2",
                "customer_id": "c4",
                "sku": "SKU-1",
                "qty": 1,
                "total_cents": 3000,
                "priority": "MEDIUM",
                "timestamp": 40,
            }
        )

        queue = engine.list_pending_fulfillments()
        self.assertEqual(
            [item["event_id"] for item in queue],
            ["evt-high-1", "evt-med-1", "evt-med-2", "evt-low-1"],
        )
        self.assertFalse(hasattr(engine, "apply_promo_discount"))
        self.assertFalse(hasattr(engine, "export_csv"))


if __name__ == "__main__":
    unittest.main()
