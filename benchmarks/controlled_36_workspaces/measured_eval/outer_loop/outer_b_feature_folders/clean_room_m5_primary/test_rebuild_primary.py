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
import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowRebuildPrimary(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_valid_and_trimming(self) -> None:
        acct = self.ledger.open_account("  acc_1  ", "USD", 5000)
        self.assertEqual(acct["account_id"], "acc_1")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 5000)
        self.assertEqual(acct["balance_cents"], 5000)
        self.assertEqual(self.ledger.get_balance("acc_1"), 5000)
        self.assertEqual(self.ledger.get_balance("  acc_1 "), 5000)

        acct_eur = self.ledger.open_account("acc_eur", "EUR", 0)
        self.assertEqual(acct_eur["currency"], "EUR")
        self.assertEqual(self.ledger.get_balance("acc_eur"), 0)

        acct_gbp = self.ledger.open_account("acc_gbp", "GBP")
        self.assertEqual(acct_gbp["currency"], "GBP")
        self.assertEqual(self.ledger.get_balance("acc_gbp"), 0)

    def test_open_account_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.ledger.open_account("", "USD", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("   ", "USD", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account(123, "USD", 0)  # type: ignore
        with self.assertRaises(ValueError):
            self.ledger.open_account("acc_1", "usd", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("acc_1", "JPY", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("acc_1", "USD", -1)
        with self.assertRaises(ValueError):
            self.ledger.open_account("acc_1", "USD", True)

        self.ledger.open_account("acc_1", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account(" acc_1 ", "USD", 200)

    def test_get_balance_unknown_account(self) -> None:
        with self.assertRaises(KeyError):
            self.ledger.get_balance("unknown")

    def test_post_transfer_settled_and_boundary(self) -> None:
        self.ledger.open_account("alice", "USD", 200_000)
        self.ledger.open_account("bob", "USD", 10_000)

        # Boundary at 100,000 cents -> SETTLED, fee = 1000
        tx = self.ledger.post_transfer("tx_100k", "alice", "bob", 100_000, 1000)
        self.assertEqual(tx["status"], "SETTLED")
        self.assertEqual(tx["fee_cents"], 1000)
        self.assertEqual(tx["amount_cents"], 100_000)
        self.assertEqual(tx["currency"], "USD")
        self.assertEqual(self.ledger.get_balance("alice"), 99_000)
        self.assertEqual(self.ledger.get_balance("bob"), 110_000)

    def test_post_transfer_pending_above_threshold(self) -> None:
        self.ledger.open_account("alice", "USD", 200_000)
        self.ledger.open_account("bob", "USD", 10_000)

        # Boundary at 100,001 cents -> PENDING, fee = 1000
        tx = self.ledger.post_transfer("tx_100k1", "alice", "bob", 100_001, 1005)
        self.assertEqual(tx["status"], "PENDING")
        self.assertEqual(tx["fee_cents"], 1000)
        self.assertEqual(self.ledger.get_balance("alice"), 200_000 - 101_001)
        self.assertEqual(self.ledger.get_balance("bob"), 10_000)

    def test_post_transfer_validation_errors(self) -> None:
        self.ledger.open_account("alice", "USD", 10_000)
        self.ledger.open_account("bob", "USD", 10_000)
        self.ledger.open_account("charlie", "EUR", 10_000)

        # Unknown accounts -> KeyError
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("t1", "unknown", "bob", 100, 1)
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("t2", "alice", "unknown", 100, 1)

        # Same account -> ValueError
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t3", "alice", "alice", 100, 1)

        # Currency mismatch -> ValueError
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t4", "alice", "charlie", 100, 1)

        # Invalid amount -> ValueError
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t5", "alice", "bob", 0, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t6", "alice", "bob", -50, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t7", "alice", "bob", True, 1)

        # Insufficient funds (10,000 amount + 100 fee = 10,100 > 10,000) -> ValueError
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t8", "alice", "bob", 10_000, 1)

        # Duplicate tx_id -> ValueError
        self.ledger.post_transfer("t_ok", "alice", "bob", 1000, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t_ok", "alice", "bob", 1000, 2)


if __name__ == "__main__":
    unittest.main()
