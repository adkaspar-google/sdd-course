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
"""Superficial unit test using mock/stub assertion without probing unbalanced legs."""

import unittest
from unittest.mock import MagicMock
from settlement_coordinator import SettlementCoordinator


class TestSettlementCoordinator(unittest.TestCase):
    def test_submit_happy_path_with_mock_verifier(self) -> None:
        sc = SettlementCoordinator()
        sc.verify_trial_balance = MagicMock(return_value=True)
        b = sc.submit_batch(
            "b1",
            [
                {"account_id": "cash", "side": "DEBIT", "amount_cents": 5000},
                {"account_id": "rev", "side": "CREDIT", "amount_cents": 5000},
            ],
        )
        self.assertEqual(b["status"], "COMMITTED")
        self.assertTrue(sc.verify_trial_balance())


if __name__ == "__main__":
    unittest.main()
