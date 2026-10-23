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
"""Unit tests for LedgerFlow Milestones 1 through 4."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowM1ToM4(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_and_get_balance_valid(self) -> None:
        acct = self.ledger.open_account("  acct_1  ", "usd", 5000)
        self.assertEqual(acct["account_id"], "acct_1")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 5000)
        self.assertEqual(self.ledger.get_balance("acct_1"), 5000)

        acct_eur = self.ledger.open_account("acct_eur", "EUR", 0)
        self.assertEqual(acct_eur["currency"], "EUR")
        self.assertEqual(self.ledger.get_balance("acct_eur"), 0)

        acct_gbp = self.ledger.open_account("acct_gbp", "GBP", 250)
        self.assertEqual(acct_gbp["currency"], "GBP")
        self.assertEqual(self.ledger.get_balance("acct_gbp"), 250)

    def test_open_account_invalid_inputs_and_duplicate(self) -> None:
        self.ledger.open_account("a1", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("a1", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("  a1  ", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("   ", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("a2", "JPY", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("a2", "US", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("a2", "USD", -1)

    def test_get_balance_unknown_account(self) -> None:
        with self.assertRaises(KeyError):
            self.ledger.get_balance("nonexistent")

    def test_tiered_fees_and_inclusive_threshold(self) -> None:
        self.ledger.open_account("alice", "USD", 500000)
        self.ledger.open_account("bob", "USD", 0)

        tx_small = self.ledger.post_transfer("tx_small", "alice", "bob", 500, 10)
        self.assertEqual(tx_small["status"], "SETTLED")
        self.assertEqual(tx_small["fee_cents"], 10)
        self.assertEqual(self.ledger.get_balance("alice"), 500000 - 510)
        self.assertEqual(self.ledger.get_balance("bob"), 500)

        tx_below = self.ledger.post_transfer("tx_below", "alice", "bob", 99999, 20)
        self.assertEqual(tx_below["status"], "SETTLED")
        self.assertEqual(tx_below["fee_cents"], 999)
        self.assertEqual(self.ledger.get_balance("alice"), 499490 - 100998)
        self.assertEqual(self.ledger.get_balance("bob"), 500 + 99999)

        tx_boundary = self.ledger.post_transfer("tx_bound", "alice", "bob", 100000, 30)
        self.assertEqual(tx_boundary["status"], "AWAITING_CLEARING")
        self.assertEqual(tx_boundary["fee_cents"], 500)
        self.assertEqual(self.ledger.get_balance("alice"), 398492 - 100500)
        self.assertEqual(self.ledger.get_balance("bob"), 100499)

    def test_clear_transfer_and_settle_pending_alias(self) -> None:
        self.ledger.open_account("alice", "EUR", 500000)
        self.ledger.open_account("bob", "EUR", 1000)

        tx1 = self.ledger.post_transfer("tx_c1", "alice", "bob", 100000, 100)
        self.assertEqual(tx1["status"], "AWAITING_CLEARING")
        self.assertEqual(tx1["fee_cents"], 500)

        cleared1 = self.ledger.clear_transfer("tx_c1")
        self.assertEqual(cleared1["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("bob"), 101000)

        tx2 = self.ledger.post_transfer("tx_c2", "alice", "bob", 200000, 110)
        self.assertEqual(tx2["status"], "AWAITING_CLEARING")
        self.assertEqual(tx2["fee_cents"], 1000)
        cleared2 = self.ledger.settle_pending("tx_c2")
        self.assertEqual(cleared2["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("bob"), 301000)

        with self.assertRaises(ValueError):
            self.ledger.clear_transfer("tx_c1")
        with self.assertRaises(ValueError):
            self.ledger.settle_pending("tx_c2")

        with self.assertRaises(KeyError):
            self.ledger.clear_transfer("unknown_tx")

    def test_idempotent_replay_and_conflicting_tx_id(self) -> None:
        self.ledger.open_account("alice", "USD", 510)
        self.ledger.open_account("bob", "USD", 0)
        self.ledger.open_account("charlie", "USD", 0)

        tx_orig = self.ledger.post_transfer("tx_idem", "alice", "bob", 500, 1000)
        self.assertEqual(self.ledger.get_balance("alice"), 0)
        self.assertEqual(self.ledger.get_balance("bob"), 500)

        tx_replay = self.ledger.post_transfer("tx_idem", "alice", "bob", 500, 2000)
        self.assertEqual(tx_replay, tx_orig)
        self.assertEqual(self.ledger.get_balance("alice"), 0)
        self.assertEqual(self.ledger.get_balance("bob"), 500)
        self.assertEqual(len(self.ledger.account_statement("alice")), 1)

        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx_idem", "alice", "bob", 600, 1000)

        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx_idem", "alice", "charlie", 500, 1000)

        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx_idem", "bob", "alice", 500, 1000)

    def test_reverse_transfer_awaiting_clearing_and_settled(self) -> None:
        self.ledger.open_account("alice", "USD", 300000)
        self.ledger.open_account("bob", "USD", 1000)
        self.ledger.open_account("charlie", "USD", 0)

        # 1. Reverse AWAITING_CLEARING transfer
        tx_await = self.ledger.post_transfer("tx_rev_await", "alice", "bob", 100000, 10)
        self.assertEqual(tx_await["status"], "AWAITING_CLEARING")
        self.assertEqual(tx_await["fee_cents"], 500)
        self.assertEqual(self.ledger.get_balance("alice"), 300000 - 100500)
        self.assertEqual(self.ledger.get_balance("bob"), 1000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 500)

        rev1 = self.ledger.reverse_transfer("tx_rev_await")
        self.assertEqual(rev1["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("alice"), 300000)
        self.assertEqual(self.ledger.get_balance("bob"), 1000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 0)

        # Cannot reverse an already reversed transfer
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer("tx_rev_await")

        # Cannot clear a reversed transfer
        with self.assertRaises(ValueError):
            self.ledger.clear_transfer("tx_rev_await")

        # 2. Reverse SETTLED transfer with sufficient recipient funds
        tx_settled = self.ledger.post_transfer("tx_rev_settled", "alice", "bob", 10000, 20)
        self.assertEqual(tx_settled["status"], "SETTLED")
        self.assertEqual(tx_settled["fee_cents"], 100)
        self.assertEqual(self.ledger.get_balance("alice"), 300000 - 10100)
        self.assertEqual(self.ledger.get_balance("bob"), 11000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 100)

        rev2 = self.ledger.reverse_transfer("tx_rev_settled")
        self.assertEqual(rev2["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("alice"), 300000)
        self.assertEqual(self.ledger.get_balance("bob"), 1000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 0)

        # 3. Reverse SETTLED transfer when recipient has insufficient funds
        self.ledger.post_transfer("tx_to_bob", "alice", "bob", 5000, 30)
        # Bob has 1000 + 5000 = 6000; Bob sends 2000 (+20 fee) to charlie -> Bob has 3980 left (< 5000)
        self.ledger.post_transfer("tx_bob_spend", "bob", "charlie", 2000, 40)
        self.assertEqual(self.ledger.get_balance("bob"), 3980)

        with self.assertRaisesRegex(ValueError, "Recipient has insufficient funds to reverse"):
            self.ledger.reverse_transfer("tx_to_bob")

        # State unchanged after failed reversal
        self.assertEqual(self.ledger.get_balance("bob"), 3980)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 50 + 20)

        # Unknown tx_id raises KeyError
        with self.assertRaises(KeyError):
            self.ledger.reverse_transfer("tx_does_not_exist")

    def test_total_collected_fees_multi_currency(self) -> None:
        self.ledger.open_account("u1", "USD", 500000)
        self.ledger.open_account("u2", "USD", 0)
        self.ledger.open_account("e1", "EUR", 500000)
        self.ledger.open_account("e2", "EUR", 0)

        self.ledger.post_transfer("u_tx1", "u1", "u2", 10000, 1)  # fee 100
        self.ledger.post_transfer("u_tx2", "u1", "u2", 100000, 2)  # fee 500 (AWAITING_CLEARING)
        self.ledger.post_transfer("e_tx1", "e1", "e2", 20000, 3)  # fee 200

        self.assertEqual(self.ledger.total_collected_fees("USD"), 600)
        self.assertEqual(self.ledger.total_collected_fees("EUR"), 200)
        self.assertEqual(self.ledger.total_collected_fees("GBP"), 0)

    def test_post_transfer_validation_errors(self) -> None:
        self.ledger.open_account("alice", "USD", 1000)
        self.ledger.open_account("bob", "USD", 500)
        self.ledger.open_account("euro_acct", "EUR", 1000)

        with self.assertRaises(KeyError):
            self.ledger.post_transfer("t1", "unknown", "bob", 100, 1)
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("t2", "alice", "unknown", 100, 1)

        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t3", "alice", "alice", 100, 1)

        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t4", "alice", "bob", 0, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t5", "alice", "bob", -50, 1)

        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t6", "alice", "euro_acct", 100, 1)

        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t7", "alice", "bob", 995, 1)

        self.assertEqual(self.ledger.get_balance("alice"), 1000)
        self.assertEqual(self.ledger.get_balance("bob"), 500)

    def test_account_statement_sorting_and_copy_isolation(self) -> None:
        self.ledger.open_account("alice", "USD", 1000000)
        self.ledger.open_account("bob", "USD", 500000)
        self.ledger.open_account("charlie", "USD", 100000)

        self.ledger.post_transfer("tx_1", "alice", "bob", 1000, 30)
        self.ledger.post_transfer("tx_2", "bob", "alice", 2000, 10)
        self.ledger.post_transfer("tx_3", "alice", "charlie", 3000, 20)
        self.ledger.post_transfer("tx_4", "charlie", "alice", 4000, 20)
        self.ledger.post_transfer("tx_5", "bob", "charlie", 500, 15)

        alice_stmt = self.ledger.account_statement("alice")
        self.assertEqual([t["tx_id"] for t in alice_stmt], ["tx_2", "tx_3", "tx_4", "tx_1"])

        alice_stmt[0]["status"] = "CORRUPTED"
        self.assertEqual(self.ledger.account_statement("alice")[0]["status"], "SETTLED")

        with self.assertRaises(KeyError):
            self.ledger.account_statement("unknown_acct")


if __name__ == "__main__":
    unittest.main()
