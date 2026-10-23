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
"""Comprehensive unit tests for clean-room LedgerFlow implementation."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowRebuildPrimary(unittest.TestCase):
    """Tests all EARS requirements REQ-M1-001 through REQ-M4-006."""

    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_and_get_balance(self) -> None:
        acct = self.ledger.open_account("  alice  ", "usd", 5000)
        self.assertEqual(acct["account_id"], "alice")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 5000)
        self.assertEqual(acct["balance_cents"], 5000)
        self.assertEqual(self.ledger.get_balance("alice"), 5000)
        self.assertEqual(self.ledger.get_balance("  alice "), 5000)
        self.assertEqual(self.ledger.accounts["alice"], 5000)

    def test_open_account_validation_errors(self) -> None:
        self.ledger.open_account("alice", "EUR", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("   ", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("alice", "EUR", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("bob", "JPY", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("bob", "USD", -1)
        with self.assertRaises(ValueError):
            self.ledger.open_account("bob", "USD", True)

    def test_get_balance_unknown_account(self) -> None:
        with self.assertRaises(KeyError):
            self.ledger.get_balance("missing")

    def test_standard_transfer_and_fee_floor(self) -> None:
        self.ledger.open_account("a", "USD", 10000)
        self.ledger.open_account("b", "USD", 0)

        # Small transfer (500 cents -> 1% is 5 cents, floor is 10 cents)
        tx1 = self.ledger.post_transfer("tx1", "a", "b", 500, 10)
        self.assertEqual(tx1["fee_cents"], 10)
        self.assertEqual(tx1["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("a"), 10000 - 510)
        self.assertEqual(self.ledger.get_balance("b"), 500)

        # Standard transfer above floor (5000 cents -> 1% is 50 cents)
        tx2 = self.ledger.post_transfer("tx2", "a", "b", 5000, 20)
        self.assertEqual(tx2["fee_cents"], 50)
        self.assertEqual(tx2["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("a"), 10000 - 510 - 5050)
        self.assertEqual(self.ledger.get_balance("b"), 5500)

    def test_high_value_transfer_awaiting_clearing_and_clear(self) -> None:
        self.ledger.open_account("a", "GBP", 500000)
        self.ledger.open_account("b", "GBP", 1000)

        # High-value transfer (100000 cents -> 50 bps = 500 cents)
        tx = self.ledger.post_transfer("tx_hv", "a", "b", 100000, 100)
        self.assertEqual(tx["fee_cents"], 500)
        self.assertEqual(tx["status"], "AWAITING_CLEARING")
        self.assertEqual(self.ledger.get_balance("a"), 500000 - 100500)
        self.assertEqual(self.ledger.get_balance("b"), 1000)

        # Clear transfer
        cleared = self.ledger.clear_transfer("tx_hv")
        self.assertEqual(cleared["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("b"), 101000)

        # Re-clearing already settled raises ValueError
        with self.assertRaises(ValueError):
            self.ledger.clear_transfer("tx_hv")

        # Unknown tx_id raises KeyError
        with self.assertRaises(KeyError):
            self.ledger.clear_transfer("unknown_tx")

    def test_settle_pending_alias(self) -> None:
        self.ledger.open_account("a", "EUR", 300000)
        self.ledger.open_account("b", "EUR", 0)
        tx = self.ledger.post_transfer("tx_alias", "a", "b", 200000, 50)
        self.assertEqual(tx["fee_cents"], 1000)
        self.assertEqual(tx["status"], "AWAITING_CLEARING")
        settled = self.ledger.settle_pending("tx_alias")
        self.assertEqual(settled["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("b"), 200000)

    def test_idempotency_and_conflicting_replay(self) -> None:
        self.ledger.open_account("a", "USD", 50000)
        self.ledger.open_account("b", "USD", 0)
        self.ledger.open_account("c", "USD", 0)

        tx1 = self.ledger.post_transfer("tx_idem", "a", "b", 2000, 100)
        bal_a = self.ledger.get_balance("a")
        bal_b = self.ledger.get_balance("b")

        # Exact replay returns copy without double debit/credit
        tx1_replay = self.ledger.post_transfer("tx_idem", "a", "b", 2000, 999)
        self.assertEqual(tx1_replay, tx1)
        self.assertEqual(self.ledger.get_balance("a"), bal_a)
        self.assertEqual(self.ledger.get_balance("b"), bal_b)
        self.assertEqual(len(self.ledger.entries), 1)

        # Conflicting amount_cents
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_idem", "a", "b", 3000, 100)
        # Conflicting to_acct
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_idem", "a", "c", 2000, 100)
        # Conflicting from_acct
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_idem", "c", "b", 2000, 100)

    def test_transfer_validation_and_no_overdraft(self) -> None:
        self.ledger.open_account("a", "USD", 1000)
        self.ledger.open_account("b", "USD", 0)
        self.ledger.open_account("e", "EUR", 1000)

        # Missing accounts -> KeyError
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("t1", "missing", "b", 100, 1)
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("t2", "a", "missing", 100, 1)

        # Same account, non-positive amount, currency mismatch, insufficient funds -> ValueError
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("", "a", "b", 100, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t3", "a", "a", 100, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t4", "a", "b", 0, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t5", "a", "b", -50, 1)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t6", "a", "e", 100, 1)
        # 1000 cents + 10 cents fee = 1010 > 1000 balance
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("t7", "a", "b", 1000, 1)
        self.assertEqual(self.ledger.get_balance("a"), 1000)

    def test_reverse_transfer_awaiting_and_settled(self) -> None:
        self.ledger.open_account("a", "USD", 500000)
        self.ledger.open_account("b", "USD", 0)
        self.ledger.open_account("c", "USD", 0)

        # Reverse AWAITING_CLEARING transfer
        tx_high = self.ledger.post_transfer("tx_high", "a", "b", 100000, 10)
        self.assertEqual(self.ledger.get_balance("a"), 399500)
        rev_high = self.ledger.reverse_transfer("tx_high")
        self.assertEqual(rev_high["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("a"), 500000)
        self.assertEqual(self.ledger.get_balance("b"), 0)

        # Reversing already reversed raises ValueError
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer("tx_high")

        # Reverse SETTLED transfer with sufficient recipient funds
        tx_low = self.ledger.post_transfer("tx_low", "a", "b", 10000, 20)
        self.assertEqual(tx_low["fee_cents"], 100)
        self.assertEqual(self.ledger.get_balance("a"), 500000 - 10100)
        self.assertEqual(self.ledger.get_balance("b"), 10000)
        rev_low = self.ledger.reverse_transfer("tx_low")
        self.assertEqual(rev_low["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("a"), 500000)
        self.assertEqual(self.ledger.get_balance("b"), 0)

        # Reverse SETTLED transfer when recipient has insufficient funds
        self.ledger.post_transfer("tx_spend", "a", "b", 10000, 30)
        self.ledger.post_transfer("tx_drain", "b", "c", 5000, 40)
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer("tx_spend")
        # State remains unchanged
        self.assertEqual(self.ledger.get_balance("b"), 10000 - 5050)

        # Unknown tx_id raises KeyError
        with self.assertRaises(KeyError):
            self.ledger.reverse_transfer("no_such_tx")

    def test_total_collected_fees(self) -> None:
        self.ledger.open_account("a", "USD", 500000)
        self.ledger.open_account("b", "USD", 50000)
        self.ledger.open_account("e1", "EUR", 100000)
        self.ledger.open_account("e2", "EUR", 0)

        self.ledger.post_transfer("u1", "a", "b", 10000, 10)  # fee 100 (SETTLED)
        self.ledger.post_transfer("u2", "a", "b", 100000, 20)  # fee 500 (AWAITING_CLEARING)
        self.ledger.post_transfer("e_tx", "e1", "e2", 5000, 30)  # fee 50 EUR

        self.assertEqual(self.ledger.total_collected_fees("USD"), 600)
        self.assertEqual(self.ledger.total_collected_fees("EUR"), 50)
        self.assertEqual(self.ledger.total_collected_fees("GBP"), 0)

        # Reversing u1 removes its 100 cent fee from collected fees
        self.ledger.reverse_transfer("u1")
        self.assertEqual(self.ledger.total_collected_fees("USD"), 500)

        with self.assertRaises(ValueError):
            self.ledger.total_collected_fees("CAD")

    def test_account_statement_ordering(self) -> None:
        self.ledger.open_account("a", "USD", 100000)
        self.ledger.open_account("b", "USD", 100000)
        self.ledger.open_account("c", "USD", 100000)

        self.ledger.post_transfer("t1", "a", "b", 1000, 50)
        self.ledger.post_transfer("t2", "b", "c", 1000, 10)
        self.ledger.post_transfer("t3", "c", "a", 1000, 20)
        self.ledger.post_transfer("t4", "a", "b", 1000, 20)

        stmt_a = self.ledger.account_statement("a")
        self.assertEqual([tx["tx_id"] for tx in stmt_a], ["t3", "t4", "t1"])

        with self.assertRaises(KeyError):
            self.ledger.account_statement("unknown")


if __name__ == "__main__":
    unittest.main()
