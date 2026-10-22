"""Unit tests for Milestones 1 through 4 of LedgerFlow."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowM1ToM4(unittest.TestCase):
    """Test suite covering M1 core ledger, M2 statements, M3 mutations, and M4 reversals/fees."""

    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_valid_and_trimmed(self) -> None:
        acct = self.ledger.open_account("  alice  ", "USD", 5000)
        self.assertEqual(acct["account_id"], "alice")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(self.ledger.get_balance("alice"), 5000)
        self.assertEqual(self.ledger.get_balance("  alice "), 5000)

        eur = self.ledger.open_account("bob", "EUR", 0)
        self.assertEqual(eur["currency"], "EUR")
        self.assertEqual(self.ledger.get_balance("bob"), 0)

        gbp = self.ledger.open_account("charlie", "GBP", 250)
        self.assertEqual(gbp["currency"], "GBP")
        self.assertEqual(self.ledger.get_balance("charlie"), 250)

    def test_open_account_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.ledger.open_account("", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("   ", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("alice", "usd", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("alice", "JPY", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("alice", "USD", -1)

        self.ledger.open_account("alice", "USD", 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account("alice", "USD", 200)
        with self.assertRaises(ValueError):
            self.ledger.open_account("  alice  ", "EUR", 0)

    def test_get_balance_unknown_account(self) -> None:
        with self.assertRaises(KeyError):
            self.ledger.get_balance("nonexistent")

    def test_tiered_fees_and_inclusive_threshold(self) -> None:
        self.ledger.open_account("a1", "USD", 500_000)
        self.ledger.open_account("a2", "USD", 0)

        tx_small = self.ledger.post_transfer("tx-small", "a1", "a2", 250, 10)
        self.assertEqual(tx_small["status"], "SETTLED")
        self.assertEqual(tx_small["fee_cents"], 10)
        self.assertEqual(self.ledger.get_balance("a1"), 500_000 - 260)
        self.assertEqual(self.ledger.get_balance("a2"), 250)

        tx_mid = self.ledger.post_transfer("tx-mid", "a1", "a2", 99_999, 20)
        self.assertEqual(tx_mid["status"], "SETTLED")
        self.assertEqual(tx_mid["fee_cents"], 999)
        self.assertEqual(self.ledger.get_balance("a2"), 250 + 99_999)

        tx_bound = self.ledger.post_transfer("tx-bound", "a1", "a2", 100_000, 30)
        self.assertEqual(tx_bound["status"], "AWAITING_CLEARING")
        self.assertEqual(tx_bound["fee_cents"], 500)
        self.assertEqual(self.ledger.get_balance("a2"), 250 + 99_999)

        cleared = self.ledger.clear_transfer("tx-bound")
        self.assertEqual(cleared["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("a2"), 250 + 99_999 + 100_000)

    def test_settle_pending_alias_and_errors(self) -> None:
        self.ledger.open_account("a1", "USD", 500_000)
        self.ledger.open_account("a2", "USD", 0)

        tx = self.ledger.post_transfer("tx-high", "a1", "a2", 200_000, 100)
        self.assertEqual(tx["status"], "AWAITING_CLEARING")
        self.assertEqual(tx["fee_cents"], 1_000)

        settled = self.ledger.settle_pending("tx-high")
        self.assertEqual(settled["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("a2"), 200_000)

        with self.assertRaises(ValueError):
            self.ledger.clear_transfer("tx-high")
        with self.assertRaises(ValueError):
            self.ledger.settle_pending("tx-high")
        with self.assertRaises(KeyError):
            self.ledger.clear_transfer("unknown-tx")

    def test_replay_safe_idempotency(self) -> None:
        self.ledger.open_account("a1", "USD", 50_000)
        self.ledger.open_account("a2", "USD", 10_000)
        self.ledger.open_account("a3", "USD", 10_000)

        tx1 = self.ledger.post_transfer("tx-idem", "a1", "a2", 5_000, 100)
        bal_a1 = self.ledger.get_balance("a1")
        bal_a2 = self.ledger.get_balance("a2")

        tx1_replay = self.ledger.post_transfer("tx-idem", "a1", "a2", 5_000, 999)
        self.assertEqual(tx1_replay, tx1)
        self.assertEqual(self.ledger.get_balance("a1"), bal_a1)
        self.assertEqual(self.ledger.get_balance("a2"), bal_a2)
        self.assertEqual(len(self.ledger.account_statement("a1")), 1)

        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx-idem", "a1", "a2", 6_000, 100)
        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx-idem", "a1", "a3", 5_000, 100)
        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx-idem", "a3", "a2", 5_000, 100)

    def test_reverse_transfer_awaiting_clearing_and_settled(self) -> None:
        self.ledger.open_account("a1", "USD", 300_000)
        self.ledger.open_account("a2", "USD", 1_000)

        # 1. Reverse an AWAITING_CLEARING transfer
        tx_hold = self.ledger.post_transfer("tx-hold", "a1", "a2", 100_000, 10)
        self.assertEqual(tx_hold["status"], "AWAITING_CLEARING")
        self.assertEqual(self.ledger.get_balance("a1"), 300_000 - 100_500)
        self.assertEqual(self.ledger.get_balance("a2"), 1_000)

        rev_hold = self.ledger.reverse_transfer("tx-hold")
        self.assertEqual(rev_hold["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("a1"), 300_000)
        self.assertEqual(self.ledger.get_balance("a2"), 1_000)

        # Cannot reverse again or clear a reversed transfer
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer("tx-hold")
        with self.assertRaises(ValueError):
            self.ledger.clear_transfer("tx-hold")

        # 2. Reverse a SETTLED transfer
        tx_settled = self.ledger.post_transfer("tx-settled", "a1", "a2", 10_000, 20)
        self.assertEqual(tx_settled["status"], "SETTLED")
        self.assertEqual(tx_settled["fee_cents"], 100)
        self.assertEqual(self.ledger.get_balance("a1"), 300_000 - 10_100)
        self.assertEqual(self.ledger.get_balance("a2"), 11_000)

        rev_settled = self.ledger.reverse_transfer("tx-settled")
        self.assertEqual(rev_settled["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("a1"), 300_000)
        self.assertEqual(self.ledger.get_balance("a2"), 1_000)

    def test_reverse_transfer_insufficient_recipient_funds_and_unknown_tx(self) -> None:
        self.ledger.open_account("a1", "USD", 50_000)
        self.ledger.open_account("a2", "USD", 0)
        self.ledger.open_account("a3", "USD", 0)

        self.ledger.post_transfer("tx-1", "a1", "a2", 10_000, 10)
        # a2 spends part of the received funds
        self.ledger.post_transfer("tx-2", "a2", "a3", 5_000, 20)

        bal_a1_before = self.ledger.get_balance("a1")
        bal_a2_before = self.ledger.get_balance("a2")

        with self.assertRaisesRegex(ValueError, "Recipient has insufficient funds to reverse"):
            self.ledger.reverse_transfer("tx-1")

        # Ensure no state was mutated
        self.assertEqual(self.ledger.get_balance("a1"), bal_a1_before)
        self.assertEqual(self.ledger.get_balance("a2"), bal_a2_before)
        self.assertEqual(self.ledger.account_statement("a1")[0]["status"], "SETTLED")

        with self.assertRaises(KeyError):
            self.ledger.reverse_transfer("nonexistent-tx")

    def test_total_collected_fees_and_overdraft_prohibition(self) -> None:
        self.ledger.open_account("u1", "USD", 500_000)
        self.ledger.open_account("u2", "USD", 10_000)
        self.ledger.open_account("e1", "EUR", 200_000)
        self.ledger.open_account("e2", "EUR", 10_000)

        # Overdraft strictly prohibited on post_transfer
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx-overdraft", "u2", "u1", 10_000, 1)

        self.ledger.post_transfer("tx-u1", "u1", "u2", 10_000, 10)   # fee = 100 (SETTLED)
        self.ledger.post_transfer("tx-u2", "u1", "u2", 100_000, 20)  # fee = 500 (AWAITING_CLEARING)
        self.ledger.post_transfer("tx-e1", "e1", "e2", 20_000, 30)   # fee = 200 (SETTLED, EUR)

        self.assertEqual(self.ledger.total_collected_fees("USD"), 600)
        self.assertEqual(self.ledger.total_collected_fees("EUR"), 200)
        self.assertEqual(self.ledger.total_collected_fees("GBP"), 0)

        # Reversing tx-u1 removes its 100-cent fee from collected total
        self.ledger.reverse_transfer("tx-u1")
        self.assertEqual(self.ledger.total_collected_fees("USD"), 500)

        # Reversing tx-u2 (AWAITING_CLEARING) removes its 500-cent fee
        self.ledger.reverse_transfer("tx-u2")
        self.assertEqual(self.ledger.total_collected_fees("USD"), 0)


if __name__ == "__main__":
    unittest.main()
