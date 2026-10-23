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
"""Comprehensive clean-room verification tests for LedgerFlow (M1-M4 specs)."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowRebuild(unittest.TestCase):
    """Tests covering M1, M2, M3, and M4 specification requirements."""

    def test_m1_open_account_and_balance(self) -> None:
        ledger = LedgerFlow()
        acct = ledger.open_account("  alice  ", "USD", 50_000)
        self.assertEqual(acct["account_id"], "alice")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 50_000)
        self.assertEqual(acct["balance_cents"], 50_000)
        self.assertEqual(ledger.get_balance("alice"), 50_000)

        with self.assertRaises(ValueError):
            ledger.open_account("alice", "USD", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("   ", "USD", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "JPY", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "USD", -1)
        with self.assertRaises(KeyError):
            ledger.get_balance("unknown")

    def test_m3_tiered_fees_and_inclusive_threshold(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a1", "USD", 500_000)
        ledger.open_account("a2", "USD", 0)

        # Small transfer < 100_000 with 10-cent floor (500 cents -> 1% is 5 -> floor 10)
        tx1 = ledger.post_transfer("tx1", "a1", "a2", 500, 100)
        self.assertEqual(tx1["status"], "SETTLED")
        self.assertEqual(tx1["fee_cents"], 10)
        self.assertEqual(ledger.get_balance("a1"), 500_000 - 510)
        self.assertEqual(ledger.get_balance("a2"), 500)

        # Standard transfer < 100_000 (10_000 cents -> 1% = 100 cents)
        tx2 = ledger.post_transfer("tx2", "a1", "a2", 10_000, 200)
        self.assertEqual(tx2["status"], "SETTLED")
        self.assertEqual(tx2["fee_cents"], 100)
        self.assertEqual(ledger.get_balance("a1"), 500_000 - 510 - 10_100)
        self.assertEqual(ledger.get_balance("a2"), 10_500)

        # Boundary transfer == 100_000 -> AWAITING_CLEARING, 50 bps = 500 cents
        tx3 = ledger.post_transfer("tx3", "a1", "a2", 100_000, 300)
        self.assertEqual(tx3["status"], "AWAITING_CLEARING")
        self.assertEqual(tx3["fee_cents"], 500)
        self.assertEqual(ledger.get_balance("a1"), 500_000 - 510 - 10_100 - 100_500)
        self.assertEqual(ledger.get_balance("a2"), 10_500)

        # Clear via clear_transfer
        cleared = ledger.clear_transfer("tx3")
        self.assertEqual(cleared["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("a2"), 110_500)

        # Backward-compatible settle_pending alias
        tx4 = ledger.post_transfer("tx4", "a1", "a2", 200_000, 400)
        self.assertEqual(tx4["status"], "AWAITING_CLEARING")
        self.assertEqual(tx4["fee_cents"], 1000)
        settled = ledger.settle_pending("tx4")
        self.assertEqual(settled["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("a2"), 310_500)

    def test_m3_idempotency_and_conflicts(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a1", "EUR", 50_000)
        ledger.open_account("a2", "EUR", 0)

        tx1 = ledger.post_transfer("tx_idem", "a1", "a2", 5_000, 10)
        bal_a1 = ledger.get_balance("a1")
        bal_a2 = ledger.get_balance("a2")

        # Exact replay returns copy without double debit/credit or duplicate statement entry
        tx1_replay = ledger.post_transfer("tx_idem", "a1", "a2", 5_000, 99)
        self.assertEqual(tx1_replay["tx_id"], "tx_idem")
        self.assertEqual(ledger.get_balance("a1"), bal_a1)
        self.assertEqual(ledger.get_balance("a2"), bal_a2)
        self.assertEqual(len(ledger.account_statement("a1")), 1)

        # Conflicting parameters raise ValueError
        with self.assertRaises(ValueError):
            ledger.post_transfer("tx_idem", "a1", "a2", 6_000, 10)
        with self.assertRaises(ValueError):
            ledger.post_transfer("tx_idem", "a2", "a1", 5_000, 10)

    def test_m2_account_statement_ordering_and_copy(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a1", "GBP", 100_000)
        ledger.open_account("a2", "GBP", 100_000)

        ledger.post_transfer("t_late", "a1", "a2", 1_000, 200)
        ledger.post_transfer("t_early_1", "a2", "a1", 2_000, 100)
        ledger.post_transfer("t_early_2", "a1", "a2", 3_000, 100)

        stmt = ledger.account_statement("a1")
        self.assertEqual([t["tx_id"] for t in stmt], ["t_early_1", "t_early_2", "t_late"])

        # Mutating returned statement does not corrupt internal state
        stmt[0]["status"] = "CORRUPTED"
        self.assertEqual(ledger.account_statement("a1")[0]["status"], "SETTLED")

    def test_m4_reversals_fees_and_overdraft(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a1", "USD", 300_000)
        ledger.open_account("a2", "USD", 0)

        # Settled transfer: 10_000 + 100 fee
        ledger.post_transfer("tx_settled", "a1", "a2", 10_000, 10)
        # High-value transfer awaiting clearing: 100_000 + 500 fee
        ledger.post_transfer("tx_awaiting", "a1", "a2", 100_000, 20)
        self.assertEqual(ledger.total_collected_fees("USD"), 600)

        # Reverse awaiting clearing -> refunds 100_500 to a1
        rev_awaiting = ledger.reverse_transfer("tx_awaiting")
        self.assertEqual(rev_awaiting["status"], "REVERSED")
        self.assertEqual(ledger.get_balance("a1"), 300_000 - 10_100)
        self.assertEqual(ledger.total_collected_fees("USD"), 100)

        # Reverse settled -> debits 10_000 from a2, refunds 10_100 to a1
        rev_settled = ledger.reverse_transfer("tx_settled")
        self.assertEqual(rev_settled["status"], "REVERSED")
        self.assertEqual(ledger.get_balance("a1"), 300_000)
        self.assertEqual(ledger.get_balance("a2"), 0)
        self.assertEqual(ledger.total_collected_fees("USD"), 0)

        # Cannot reverse already reversed
        with self.assertRaises(ValueError):
            ledger.reverse_transfer("tx_settled")

        # Cannot reverse settled if recipient spent the funds
        ledger.open_account("a3", "USD", 0)
        ledger.post_transfer("tx_s2", "a1", "a2", 20_000, 30)
        ledger.post_transfer("tx_drain", "a2", "a3", 15_000, 40)
        with self.assertRaises(ValueError):
            ledger.reverse_transfer("tx_s2")


if __name__ == "__main__":
    unittest.main()
