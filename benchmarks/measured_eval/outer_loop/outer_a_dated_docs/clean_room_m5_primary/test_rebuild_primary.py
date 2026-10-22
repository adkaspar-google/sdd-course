"""Unit tests for Clean-Room Rebuild of LedgerFlow from primary specification."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowRebuildPrimary(unittest.TestCase):
    """Tests all documented rules in 2026-10-01-milestone-1.md."""

    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_and_get_balance(self) -> None:
        acct = self.ledger.open_account("  acct_1  ", "USD", 50000)
        self.assertEqual(acct["account_id"], "acct_1")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 50000)
        self.assertEqual(acct["balance_cents"], 50000)
        self.assertEqual(self.ledger.get_balance("acct_1"), 50000)

    def test_open_account_validation(self) -> None:
        self.ledger.open_account("acct_1", "EUR", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("acct_1", "EUR", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("   ", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("acct_2", "JPY", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("acct_2", "USD", -1)

    def test_get_balance_unknown_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.ledger.get_balance("missing")

    def test_post_transfer_settled_and_pending(self) -> None:
        self.ledger.open_account("alice", "USD", 500000)
        self.ledger.open_account("bob", "USD", 10000)

        # <= 100000 settles immediately with 1% fee
        tx1 = self.ledger.post_transfer("tx_1", "alice", "bob", 100000, 1700000000)
        self.assertEqual(tx1["status"], "SETTLED")
        self.assertEqual(tx1["fee_cents"], 1000)
        self.assertEqual(self.ledger.get_balance("alice"), 500000 - 101000)
        self.assertEqual(self.ledger.get_balance("bob"), 110000)

        # > 100000 is PENDING, debits sender immediately, does not credit receiver yet
        tx2 = self.ledger.post_transfer("tx_2", "alice", "bob", 150000, 1700000010)
        self.assertEqual(tx2["status"], "PENDING")
        self.assertEqual(tx2["fee_cents"], 1500)
        self.assertEqual(self.ledger.get_balance("alice"), 399000 - 151500)
        self.assertEqual(self.ledger.get_balance("bob"), 110000)

    def test_post_transfer_validation(self) -> None:
        self.ledger.open_account("alice", "USD", 10000)
        self.ledger.open_account("bob", "USD", 10000)
        self.ledger.open_account("euro_acct", "EUR", 10000)

        with self.assertRaises(KeyError):
            self.ledger.post_transfer("tx_err1", "unknown", "bob", 1000, 100)
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("tx_err2", "alice", "unknown", 1000, 100)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_err3", "alice", "alice", 1000, 100)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_err4", "alice", "bob", 0, 100)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_err5", "alice", "euro_acct", 1000, 100)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_err6", "alice", "bob", 10000, 100)  # Needs 10100

        self.ledger.post_transfer("tx_dup", "alice", "bob", 1000, 100)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_dup", "alice", "bob", 1000, 101)


if __name__ == "__main__":
    unittest.main()
