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
"""Unit tests for EscrowDisputeResolver."""

import unittest
from escrow_dispute_resolver import EscrowDisputeResolver


class TestEscrowDisputeResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.edr = EscrowDisputeResolver()

    def test_create_and_resolve_odd_cent_remainder_to_buyer(self) -> None:
        self.edr.create_escrow("e1", "m1", 101, freeze_start=10, freeze_end=20)
        res = self.edr.resolve_dispute("e1", buyer_bps=5000, seller_bps=5000, timestamp=25)
        self.assertEqual(res["buyer_refund_cents"], 51)
        self.assertEqual(res["seller_payout_cents"], 50)
        self.assertEqual(self.edr.merchant_Wallets["m1"]["available_cents"], 50)
        self.assertEqual(self.edr.merchant_Wallets["m1"]["held_cents"], 0)

    def test_inclusive_freeze_window_boundaries(self) -> None:
        self.edr.create_escrow("e1", "m1", 1000, freeze_start=100, freeze_end=200)
        with self.assertRaises(ValueError):
            self.edr.resolve_dispute("e1", 5000, 5000, timestamp=100)
        with self.assertRaises(ValueError):
            self.edr.resolve_dispute("e1", 5000, 5000, timestamp=200)
        res = self.edr.resolve_dispute("e1", 5000, 5000, timestamp=201)
        self.assertEqual(res["status"], "RESOLVED")

    def test_chargeback_deducts_held_before_available(self) -> None:
        self.edr.create_escrow("e1", "m1", 1000, freeze_start=10, freeze_end=20)
        self.edr.resolve_dispute("e1", buyer_bps=0, seller_bps=10000, timestamp=30)
        self.edr.create_escrow("e2", "m1", 600, freeze_start=40, freeze_end=50)
        # held=600, available=1000; clawback 800 -> held becomes 0, available becomes 800
        w = self.edr.apply_chargeback("m1", 800)
        self.assertEqual(w["held_cents"], 0)
        self.assertEqual(w["available_cents"], 800)

    def test_validation_guards_amount_and_bps_sum(self) -> None:
        with self.assertRaises(ValueError):
            self.edr.create_escrow("e_zero", "m1", 0, freeze_start=10, freeze_end=20)
        self.edr.create_escrow("e_bps", "m1", 100, freeze_start=10, freeze_end=20)
        with self.assertRaises(ValueError):
            self.edr.resolve_dispute("e_bps", buyer_bps=4000, seller_bps=5000, timestamp=30)


if __name__ == "__main__":
    unittest.main()
