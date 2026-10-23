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
"""Unit tests for SettlementCoordinator."""

import unittest
from settlement_coordinator import SettlementCoordinator


class TestSettlementCoordinator(unittest.TestCase):
    def setUp(self) -> None:
        self.sc = SettlementCoordinator()

    def test_balanced_batch_and_deterministic_seal(self) -> None:
        b = self.sc.submit_batch(
            "b1",
            [
                {"account_id": "cash", "side": "DEBIT", "amount_cents": 5000},
                {"account_id": "rev", "side": "CREDIT", "amount_cents": 5000},
            ],
        )
        self.assertEqual(b["volume_cents"], 5000)
        self.assertEqual(len(b["seal"]), 16)
        self.assertNotEqual(b["seal"], "0000000000000000")
        self.assertEqual(self.sc.account_postings["cash"], -5000)
        self.assertEqual(self.sc.account_postings["rev"], 5000)
        self.assertTrue(self.sc.verify_trial_balance())

    def test_unbalanced_batch_rejected_atomically(self) -> None:
        with self.assertRaises(ValueError):
            self.sc.submit_batch(
                "b_bad",
                [
                    {"account_id": "cash", "side": "DEBIT", "amount_cents": 5000},
                    {"account_id": "rev", "side": "CREDIT", "amount_cents": 4999},
                ],
            )
        self.assertEqual(self.sc.account_postings, {})

    def test_leg_count_and_zero_amount_guards(self) -> None:
        with self.assertRaises(ValueError):
            self.sc.submit_batch(
                "b_single",
                [{"account_id": "cash", "side": "DEBIT", "amount_cents": 100}],
            )
        with self.assertRaises(ValueError):
            self.sc.submit_batch(
                "b_zero",
                [
                    {"account_id": "cash", "side": "DEBIT", "amount_cents": 0},
                    {"account_id": "rev", "side": "CREDIT", "amount_cents": 0},
                ],
            )


if __name__ == "__main__":
    unittest.main()
