"""Unit tests for Milestone 1 through Milestone 4 of LedgerFlow."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowM4(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_and_get_balance(self) -> None:
        acct = self.ledger.open_account("  alice  ", "USD", 10000)
        self.assertEqual(acct["account_id"], "alice")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(self.ledger.get_balance("alice"), 10000)

    def test_tiered_fees_and_min_floor(self) -> None:
        self.ledger.open_account("alice", "USD", 500000)
        self.ledger.open_account("bob", "USD", 0)

        tx_small = self.ledger.post_transfer("tx_small", "alice", "bob", 500, 10)
        self.assertEqual(tx_small["fee_cents"], 10)
        self.assertEqual(tx_small["status"], "SETTLED")

        tx_high = self.ledger.post_transfer("tx_high", "alice", "bob", 100000, 30)
        self.assertEqual(tx_high["fee_cents"], 500)
        self.assertEqual(tx_high["status"], "AWAITING_CLEARING")

    def test_reverse_awaiting_clearing_transfer(self) -> None:
        self.ledger.open_account("alice", "USD", 200000)
        self.ledger.open_account("bob", "USD", 1000)

        tx = self.ledger.post_transfer("tx_ac", "alice", "bob", 100000, 10)
        self.assertEqual(tx["status"], "AWAITING_CLEARING")
        self.assertEqual(self.ledger.get_balance("alice"), 200000 - 100500)
        self.assertEqual(self.ledger.get_balance("bob"), 1000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 500)

        rev = self.ledger.reverse_transfer("tx_ac")
        self.assertEqual(rev["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("alice"), 200000)
        self.assertEqual(self.ledger.get_balance("bob"), 1000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 0)

        # Reversing again raises ValueError
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer("tx_ac")

    def test_reverse_settled_transfer_and_insufficient_recipient_funds(self) -> None:
        self.ledger.open_account("alice", "USD", 50000)
        self.ledger.open_account("bob", "USD", 0)
        self.ledger.open_account("charlie", "USD", 0)

        tx1 = self.ledger.post_transfer("tx_s1", "alice", "bob", 10000, 10)
        self.assertEqual(tx1["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("alice"), 50000 - 10100)
        self.assertEqual(self.ledger.get_balance("bob"), 10000)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 100)

        # Bob spends part of his balance so he cannot cover full reversal of tx_s1
        self.ledger.post_transfer("tx_s2", "bob", "charlie", 5000, 20)
        self.assertEqual(self.ledger.get_balance("bob"), 10000 - 5050)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 150)

        with self.assertRaisesRegex(
            ValueError, "Recipient has insufficient funds to reverse"
        ):
            self.ledger.reverse_transfer("tx_s1")

        # State unchanged after failed reversal
        self.assertEqual(self.ledger.get_balance("alice"), 50000 - 10100)
        self.assertEqual(self.ledger.get_balance("bob"), 10000 - 5050)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 150)

        # Reverse tx_s2 first (Charlie has 5000), then reverse tx_s1
        rev2 = self.ledger.reverse_transfer("tx_s2")
        self.assertEqual(rev2["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("bob"), 10000)
        self.assertEqual(self.ledger.get_balance("charlie"), 0)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 100)

        rev1 = self.ledger.reverse_transfer("tx_s1")
        self.assertEqual(rev1["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("alice"), 50000)
        self.assertEqual(self.ledger.get_balance("bob"), 0)
        self.assertEqual(self.ledger.total_collected_fees("USD"), 0)

    def test_total_collected_fees_multi_currency(self) -> None:
        self.ledger.open_account("a_usd", "USD", 100000)
        self.ledger.open_account("b_usd", "USD", 0)
        self.ledger.open_account("a_eur", "EUR", 100000)
        self.ledger.open_account("b_eur", "EUR", 0)

        self.ledger.post_transfer("t_u1", "a_usd", "b_usd", 10000, 1)
        self.ledger.post_transfer("t_e1", "a_eur", "b_eur", 20000, 2)

        self.assertEqual(self.ledger.total_collected_fees("USD"), 100)
        self.assertEqual(self.ledger.total_collected_fees("EUR"), 200)
        self.assertEqual(self.ledger.total_collected_fees("GBP"), 0)

    def test_overdraft_strictly_prohibited(self) -> None:
        self.ledger.open_account("alice", "USD", 1000)
        self.ledger.open_account("bob", "USD", 0)

        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_od", "alice", "bob", 1000, 1)


if __name__ == "__main__":
    unittest.main()
