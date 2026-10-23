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
"""Adversarial boundary and behavioral verification suite for OrderPulseEngine."""

from pathlib import Path
import unittest

from order_pulse import (
    DownstreamServiceError,
    OrderPulseEngine,
    RateLimitExceededError,
)


class TestOrderPulseEngine(unittest.TestCase):
    """Covers REQ-0001..REQ-0005 and all boundary equivalence classes."""

    def test_req_0001_idempotency_duplicate_event_id_returns_copy_without_side_effects(
        self,
    ) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-A": 10})
        event = {
            "event_id": "evt-001",
            "customer_id": "cust-1",
            "sku": "SKU-A",
            "qty": 3,
            "total_cents": 25000,
            "priority": "MEDIUM",
            "timestamp": 1000,
        }
        first = engine.process_order(event)
        self.assertEqual(first["status"], "CONFIRMED")
        self.assertEqual(engine.stock["SKU-A"], 7)

        # Mutate returned dict to verify a copy was returned and internal state is protected
        first["qty"] = 999

        # Replay duplicate event_id even with altered payload fields or simulated failures
        duplicate_event = {
            "event_id": "evt-001",
            "customer_id": "cust-1",
            "sku": "SKU-A",
            "qty": 10,
            "total_cents": 500000,
            "simulate_billing_failure": True,
            "timestamp": 1005,
        }
        second = engine.process_order(duplicate_event)
        self.assertEqual(second["event_id"], "evt-001")
        self.assertEqual(second["qty"], 3)
        self.assertEqual(engine.stock["SKU-A"], 7)
        self.assertEqual(len(engine.orders), 1)
        self.assertEqual(len(engine.charges), 1)
        self.assertEqual(len(engine.slack_messages), 1)
        self.assertEqual(
            engine.audit_log, [{"event_id": "evt-001", "status": "CONFIRMED"}]
        )

    def test_req_0002_validation_and_transactional_rollback_on_billing_and_slack_failure(
        self,
    ) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-A": 5})

        # Invalid qty <= 0
        with self.assertRaises(ValueError):
            engine.process_order(
                {
                    "event_id": "evt-zero",
                    "customer_id": "cust-1",
                    "sku": "SKU-A",
                    "qty": 0,
                    "total_cents": 1000,
                    "timestamp": 10,
                }
            )
        self.assertEqual(engine.stock["SKU-A"], 5)
        self.assertEqual(len(engine.audit_log), 0)

        # Insufficient stock
        with self.assertRaises(ValueError):
            engine.process_order(
                {
                    "event_id": "evt-nostock",
                    "customer_id": "cust-1",
                    "sku": "SKU-A",
                    "qty": 6,
                    "total_cents": 1000,
                    "timestamp": 10,
                }
            )
        self.assertEqual(engine.stock["SKU-A"], 5)
        self.assertEqual(len(engine.audit_log), 0)

        # Simulated billing failure: must leave stock intact, zero charges/orders/slack, and log ROLLED_BACK
        with self.assertRaises(DownstreamServiceError):
            engine.process_order(
                {
                    "event_id": "evt-bill-fail",
                    "customer_id": "cust-1",
                    "sku": "SKU-A",
                    "qty": 2,
                    "total_cents": 15000,
                    "timestamp": 20,
                    "simulate_billing_failure": True,
                }
            )
        self.assertEqual(engine.stock["SKU-A"], 5)
        self.assertEqual(len(engine.charges), 0)
        self.assertEqual(len(engine.slack_messages), 0)
        self.assertEqual(len(engine.orders), 0)
        self.assertEqual(
            engine.audit_log,
            [{"event_id": "evt-bill-fail", "status": "ROLLED_BACK"}],
        )

        # Simulated slack failure: must roll back stock AND charge, and log ROLLED_BACK
        with self.assertRaises(DownstreamServiceError):
            engine.process_order(
                {
                    "event_id": "evt-slack-fail",
                    "customer_id": "cust-1",
                    "sku": "SKU-A",
                    "qty": 3,
                    "total_cents": 25000,
                    "timestamp": 30,
                    "simulate_slack_failure": True,
                }
            )
        self.assertEqual(engine.stock["SKU-A"], 5)
        self.assertEqual(len(engine.charges), 0)
        self.assertEqual(len(engine.slack_messages), 0)
        self.assertEqual(len(engine.orders), 0)
        self.assertEqual(
            engine.audit_log,
            [
                {"event_id": "evt-bill-fail", "status": "ROLLED_BACK"},
                {"event_id": "evt-slack-fail", "status": "ROLLED_BACK"},
            ],
        )

    def test_req_0003_vip_routing_and_priority_promotion_exact_boundaries(
        self,
    ) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-VIP": 20})

        # Boundary 1: total_cents == 99999 -> #orders and preserves original priority ("LOW")
        res_below = engine.process_order(
            {
                "event_id": "evt-99999",
                "customer_id": "cust-vip",
                "sku": "SKU-VIP",
                "qty": 1,
                "total_cents": 99999,
                "priority": "LOW",
                "timestamp": 100,
            }
        )
        self.assertEqual(res_below["channel"], "#orders")
        self.assertEqual(res_below["priority"], "LOW")
        self.assertEqual(engine.slack_messages[-1]["channel"], "#orders")
        self.assertEqual(engine.slack_messages[-1]["priority"], "LOW")

        # Boundary 2: total_cents == 100000 -> #vip-orders and promoted to "HIGH"
        res_exact = engine.process_order(
            {
                "event_id": "evt-100000",
                "customer_id": "cust-vip",
                "sku": "SKU-VIP",
                "qty": 1,
                "total_cents": 100000,
                "priority": "LOW",
                "timestamp": 110,
            }
        )
        self.assertEqual(res_exact["channel"], "#vip-orders")
        self.assertEqual(res_exact["priority"], "HIGH")
        self.assertEqual(engine.slack_messages[-1]["channel"], "#vip-orders")
        self.assertEqual(engine.slack_messages[-1]["priority"], "HIGH")

    def test_req_0004_sliding_window_rate_limit_exact_60_vs_61_and_failed_excluded(
        self,
    ) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-R": 50})

        # Failed events must NOT count toward the customer's rate limit
        for i in range(2):
            with self.assertRaises(DownstreamServiceError):
                engine.process_order(
                    {
                        "event_id": f"evt-failed-{i}",
                        "customer_id": "cust-rl",
                        "sku": "SKU-R",
                        "qty": 1,
                        "total_cents": 1000,
                        "timestamp": 100,
                        "simulate_billing_failure": True,
                    }
                )

        # 3 confirmed orders at t=100, t=120, t=140
        for idx, ts in enumerate([100, 120, 140], start=1):
            engine.process_order(
                {
                    "event_id": f"evt-ok-{idx}",
                    "customer_id": "cust-rl",
                    "sku": "SKU-R",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": ts,
                }
            )

        stock_before = engine.stock["SKU-R"]
        audit_len_before = len(engine.audit_log)

        # Exact inclusive boundary: t=160 (160 - 100 == 60) -> 3 orders in [100, 160] -> RateLimitExceededError
        with self.assertRaises(RateLimitExceededError):
            engine.process_order(
                {
                    "event_id": "evt-blocked-60",
                    "customer_id": "cust-rl",
                    "sku": "SKU-R",
                    "qty": 1,
                    "total_cents": 1000,
                    "timestamp": 160,
                }
            )
        # Zero side effects on rate limit rejection
        self.assertEqual(engine.stock["SKU-R"], stock_before)
        self.assertEqual(len(engine.orders), 3)
        self.assertEqual(len(engine.charges), 3)
        self.assertEqual(len(engine.slack_messages), 3)
        self.assertEqual(len(engine.audit_log), audit_len_before)

        # Another customer at t=160 is unaffected
        other = engine.process_order(
            {
                "event_id": "evt-other-cust",
                "customer_id": "cust-other",
                "sku": "SKU-R",
                "qty": 1,
                "total_cents": 1000,
                "timestamp": 160,
            }
        )
        self.assertEqual(other["status"], "CONFIRMED")

        # Immediately outside window: t=161 (161 - 100 == 61) -> only 2 orders in [101, 161] -> allowed
        allowed = engine.process_order(
            {
                "event_id": "evt-allowed-61",
                "customer_id": "cust-rl",
                "sku": "SKU-R",
                "qty": 1,
                "total_cents": 1000,
                "timestamp": 161,
            }
        )
        self.assertEqual(allowed["status"], "CONFIRMED")

    def test_req_0005_priority_queue_fifo_stability_and_out_of_scope_guard(
        self,
    ) -> None:
        engine = OrderPulseEngine(initial_stock={"SKU-Q": 100})
        sequence = [
            ("e1", "cust-1", "LOW", 5000),
            ("e2", "cust-2", "MEDIUM", 5000),
            ("e3", "cust-3", "HIGH", 5000),
            ("e4", "cust-4", "MEDIUM", 5000),
            ("e5", "cust-5", "LOW", 100000),  # VIP promoted to HIGH
            ("e6", "cust-6", "LOW", 5000),
        ]
        for idx, (eid, cid, prio, cents) in enumerate(sequence):
            engine.process_order(
                {
                    "event_id": eid,
                    "customer_id": cid,
                    "sku": "SKU-Q",
                    "qty": 1,
                    "total_cents": cents,
                    "priority": prio,
                    "timestamp": 200 + idx,
                }
            )

        pending = engine.list_pending_fulfillments()
        self.assertEqual(
            [o["event_id"] for o in pending],
            ["e3", "e5", "e2", "e4", "e1", "e6"],
        )

        # Out-of-Scope guard: neither apply_promo_discount nor export_csv nor TODO comments may exist
        self.assertFalse(hasattr(engine, "apply_promo_discount"))
        self.assertFalse(hasattr(engine, "export_csv"))
        self.assertFalse(hasattr(OrderPulseEngine, "apply_promo_discount"))
        self.assertFalse(hasattr(OrderPulseEngine, "export_csv"))

        source_text = (
            Path(__file__).resolve().parent / "order_pulse.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("apply_promo_discount", source_text)
        self.assertNotIn("export_csv", source_text)
        self.assertNotIn("TODO", source_text)


if __name__ == "__main__":
    unittest.main()
