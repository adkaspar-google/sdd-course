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
"""Clean-room verification test suite for LedgerFlow against EARS requirements."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowRebuild(unittest.TestCase):
    """Verifies all EARS requirements across M1-M4 specifications."""

    def test_open_account_and_get_balance(self) -> None:
        ledger = LedgerFlow()
        acct = ledger.open_account("  alice  ", "usd", 50000)
        self.assertEqual(acct["account_id"], "alice")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 50000)
        self.assertEqual(ledger.get_balance("alice"), 50000)

        with self.assertRaises(ValueError):
            ledger.open_account("   ", "USD", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("alice", "USD", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "JPY", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "USD", -1)
        with self.assertRaises(KeyError):
            ledger.get_balance("unknown")

    def test_post_transfer_tiered_fees_and_thresholds(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a", "USD", 500000)
        ledger.open_account("b", "USD", 0)

        # Standard tier (< 100000): 100 bps with 10-cent floor -> SETTLED
        tx1 = ledger.post_transfer("tx1", "a", "b", 500, 10)
        self.assertEqual(tx1["fee_cents"], 10)
        self.assertEqual(tx1["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("a"), 500000 - 510)
        self.assertEqual(ledger.get_balance("b"), 500)

        # High-value tier (>= 100000): 50 bps -> AWAITING_CLEARING
        tx2 = ledger.post_transfer("tx2", "a", "b", 100000, 20)
        self.assertEqual(tx2["fee_cents"], 500)
        self.assertEqual(tx2["status"], "AWAITING_CLEARING")
        self.assertEqual(ledger.get_balance("a"), 500000 - 510 - 100500)
        self.assertEqual(ledger.get_balance("b"), 500)

    def test_idempotency_and_conflict(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a", "EUR", 20000)
        ledger.open_account("b", "EUR", 0)

        tx1 = ledger.post_transfer("tx-idem", "a", "b", 5000, 100)
        bal_a = ledger.get_balance("a")
        bal_b = ledger.get_balance("b")

        replay = ledger.post_transfer("tx-idem", "a", "b", 5000, 999)
        self.assertEqual(replay["tx_id"], tx1["tx_id"])
        self.assertEqual(ledger.get_balance("a"), bal_a)
        self.assertEqual(ledger.get_balance("b"), bal_b)

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-idem", "a", "b", 6000, 100)

    def test_clearing_and_statements(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a", "GBP", 300000)
        ledger.open_account("b", "GBP", 0)

        ledger.post_transfer("tx-late", "a", "b", 2000, 50)
        ledger.post_transfer("tx-early-1", "a", "b", 100000, 10)
        ledger.post_transfer("tx-early-2", "a", "b", 3000, 10)

        cleared = ledger.clear_transfer("tx-early-1")
        self.assertEqual(cleared["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("b"), 2000 + 3000 + 100000)

        with self.assertRaises(ValueError):
            ledger.settle_pending("tx-early-1")
        with self.assertRaises(KeyError):
            ledger.clear_transfer("no-such-tx")

        stmt = ledger.account_statement("a")
        self.assertEqual(
            [e["tx_id"] for e in stmt], ["tx-early-1", "tx-early-2", "tx-late"]
        )

    def test_reversals_and_collected_fees(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a", "USD", 500000)
        ledger.open_account("b", "USD", 0)
        ledger.open_account("c", "USD", 0)

        # Settled transfer: 10000 cents, fee 100
        ledger.post_transfer("tx-s", "a", "b", 10000, 1)
        # Awaiting clearing transfer: 200000 cents, fee 1000
        ledger.post_transfer("tx-p", "a", "b", 200000, 2)
        self.assertEqual(ledger.total_collected_fees("USD"), 1100)

        # Reverse awaiting clearing
        rev_p = ledger.reverse_transfer("tx-p")
        self.assertEqual(rev_p["status"], "REVERSED")
        self.assertEqual(ledger.total_collected_fees("USD"), 100)
        self.assertEqual(ledger.get_balance("a"), 500000 - 10100)

        # Reverse settled when recipient has funds
        rev_s = ledger.reverse_transfer("tx-s")
        self.assertEqual(rev_s["status"], "REVERSED")
        self.assertEqual(ledger.total_collected_fees("USD"), 0)
        self.assertEqual(ledger.get_balance("a"), 500000)
        self.assertEqual(ledger.get_balance("b"), 0)

        # Double reversal rejected
        with self.assertRaises(ValueError):
            ledger.reverse_transfer("tx-s")

        # Insufficient recipient funds to reverse settled transfer
        ledger.post_transfer("tx-s2", "a", "b", 10000, 3)
        ledger.post_transfer("tx-drain", "b", "c", 9500, 4)
        with self.assertRaises(ValueError):
            ledger.reverse_transfer("tx-s2")


if __name__ == "__main__":
    unittest.main()
