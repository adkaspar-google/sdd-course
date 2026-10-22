"""Locked Unit Test Suite for LedgerFlow — Milestones 1 through 4."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowM1ToM4(unittest.TestCase):
    """Comprehensive verification of M1–M4 accounts, tiered fees, clearing, reversals, fee totals, and statements."""

    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_open_account_valid_and_trimmed(self) -> None:
        acct = self.ledger.open_account("  alice_usd  ", "USD", 10000)
        self.assertEqual(acct["account_id"], "alice_usd")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(self.ledger.get_balance("alice_usd"), 10000)

        eur_acct = self.ledger.open_account("bob_eur", "EUR", 0)
        self.assertEqual(eur_acct["currency"], "EUR")
        self.assertEqual(self.ledger.get_balance("bob_eur"), 0)

        gbp_acct = self.ledger.open_account("carol_gbp", "GBP", 500)
        self.assertEqual(gbp_acct["currency"], "GBP")
        self.assertEqual(self.ledger.get_balance("carol_gbp"), 500)

    def test_open_account_invalid_inputs_and_duplicates(self) -> None:
        self.ledger.open_account("alice", "USD", 1000)
        with self.assertRaises(ValueError):
            self.ledger.open_account("alice", "USD", 500)
        with self.assertRaises(ValueError):
            self.ledger.open_account("  alice ", "EUR", 500)
        with self.assertRaises(ValueError):
            self.ledger.open_account("", "USD", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("   ", "USD", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("dave", "usd", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("dave", "CAD", 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account("dave", "USD", -1)

    def test_get_balance_unknown_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.ledger.get_balance("nonexistent")

    def test_post_transfer_below_100k_settled_with_100bps_and_10c_floor(self) -> None:
        self.ledger.open_account("alice", "USD", 200000)
        self.ledger.open_account("bob", "USD", 10000)

        tx = self.ledger.post_transfer("tx_99k", "alice", "bob", 99999, 1700000000)
        self.assertEqual(tx["status"], "SETTLED")
        self.assertEqual(tx["fee_cents"], 999)
        self.assertEqual(tx["amount_cents"], 99999)
        self.assertEqual(self.ledger.get_balance("alice"), 200000 - 100998)
        self.assertEqual(self.ledger.get_balance("bob"), 10000 + 99999)

    def test_post_transfer_small_amount_enforces_10_cent_minimum_fee(self) -> None:
        self.ledger.open_account("alice", "EUR", 109)
        self.ledger.open_account("bob", "EUR", 0)

        tx = self.ledger.post_transfer("tx_small", "alice", "bob", 99, 1700000100)
        self.assertEqual(tx["status"], "SETTLED")
        self.assertEqual(tx["fee_cents"], 10)
        self.assertEqual(self.ledger.get_balance("alice"), 0)
        self.assertEqual(self.ledger.get_balance("bob"), 99)

    def test_post_transfer_inclusive_100k_threshold_awaiting_clearing_and_50bps_fee(self) -> None:
        self.ledger.open_account("alice", "USD", 300000)
        self.ledger.open_account("bob", "USD", 10000)

        tx = self.ledger.post_transfer("tx_100k", "alice", "bob", 100000, 1700000050)
        self.assertEqual(tx["status"], "AWAITING_CLEARING")
        self.assertEqual(tx["fee_cents"], 500)
        self.assertEqual(self.ledger.get_balance("alice"), 300000 - 100500)
        self.assertEqual(self.ledger.get_balance("bob"), 10000)

    def test_clear_transfer_and_settle_pending_alias(self) -> None:
        self.ledger.open_account("alice", "USD", 500000)
        self.ledger.open_account("bob", "USD", 20000)

        tx1 = self.ledger.post_transfer("tx_c1", "alice", "bob", 100000, 1700000100)
        self.assertEqual(tx1["status"], "AWAITING_CLEARING")
        cleared1 = self.ledger.clear_transfer("tx_c1")
        self.assertEqual(cleared1["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("bob"), 120000)

        tx2 = self.ledger.post_transfer("tx_c2", "alice", "bob", 150000, 1700000200)
        self.assertEqual(tx2["status"], "AWAITING_CLEARING")
        self.assertEqual(tx2["fee_cents"], 750)
        cleared2 = self.ledger.settle_pending("tx_c2")
        self.assertEqual(cleared2["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("bob"), 270000)

        with self.assertRaises(ValueError):
            self.ledger.clear_transfer("tx_c1")
        with self.assertRaises(ValueError):
            self.ledger.settle_pending("tx_c2")
        with self.assertRaises(KeyError):
            self.ledger.clear_transfer("unknown_tx")

    def test_replay_safe_idempotency_and_conflicting_tx_id(self) -> None:
        self.ledger.open_account("alice", "USD", 100000)
        self.ledger.open_account("bob", "USD", 5000)
        self.ledger.open_account("carol", "USD", 5000)

        self.ledger.post_transfer("tx_idem", "alice", "bob", 50000, 1700000000)
        self.assertEqual(self.ledger.get_balance("alice"), 100000 - 50500)
        self.assertEqual(self.ledger.get_balance("bob"), 55000)

        tx1_replay = self.ledger.post_transfer("tx_idem", "alice", "bob", 50000, 1700000999)
        self.assertEqual(tx1_replay["tx_id"], "tx_idem")
        self.assertEqual(tx1_replay["amount_cents"], 50000)
        self.assertEqual(self.ledger.get_balance("alice"), 100000 - 50500)
        self.assertEqual(self.ledger.get_balance("bob"), 55000)
        self.assertEqual(len(self.ledger.account_statement("alice")), 1)

        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx_idem", "alice", "bob", 60000, 1700000000)
        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx_idem", "alice", "carol", 50000, 1700000000)
        with self.assertRaisesRegex(ValueError, "Conflicting tx_id"):
            self.ledger.post_transfer("tx_idem", "carol", "bob", 50000, 1700000000)

    def test_reverse_transfer_awaiting_clearing_and_settled(self) -> None:
        self.ledger.open_account("alice", "USD", 300000)
        self.ledger.open_account("bob", "USD", 10000)

        # 1. Reverse an AWAITING_CLEARING transfer
        tx_hold = self.ledger.post_transfer("tx_hold", "alice", "bob", 100000, 1700000010)
        self.assertEqual(tx_hold["status"], "AWAITING_CLEARING")
        self.assertEqual(self.ledger.get_balance("alice"), 300000 - 100500)
        self.assertEqual(self.ledger.get_balance("bob"), 10000)

        rev_hold = self.ledger.reverse_transfer("tx_hold")
        self.assertEqual(rev_hold["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("alice"), 300000)
        self.assertEqual(self.ledger.get_balance("bob"), 10000)

        # Re-reversing must raise ValueError
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer("tx_hold")

        # 2. Reverse a SETTLED transfer
        tx_settled = self.ledger.post_transfer("tx_settled", "alice", "bob", 50000, 1700000020)
        self.assertEqual(tx_settled["status"], "SETTLED")
        self.assertEqual(self.ledger.get_balance("alice"), 300000 - 50500)
        self.assertEqual(self.ledger.get_balance("bob"), 60000)

        rev_settled = self.ledger.reverse_transfer("tx_settled")
        self.assertEqual(rev_settled["status"], "REVERSED")
        self.assertEqual(self.ledger.get_balance("alice"), 300000)
        self.assertEqual(self.ledger.get_balance("bob"), 10000)

    def test_reverse_transfer_insufficient_recipient_funds_and_unknown_tx(self) -> None:
        self.ledger.open_account("alice", "USD", 100000)
        self.ledger.open_account("bob", "USD", 0)
        self.ledger.open_account("carol", "USD", 0)

        self.ledger.post_transfer("tx_1", "alice", "bob", 50000, 1700000000)
        # Bob transfers 40000 to Carol, leaving Bob with 50000 - 40400 = 9600 (< 50000)
        self.ledger.post_transfer("tx_2", "bob", "carol", 40000, 1700000010)
        self.assertEqual(self.ledger.get_balance("bob"), 9600)

        with self.assertRaisesRegex(ValueError, "Recipient has insufficient funds to reverse"):
            self.ledger.reverse_transfer("tx_1")

        # Verify no state mutation occurred on failed reversal
        self.assertEqual(self.ledger.get_balance("bob"), 9600)
        self.assertEqual(self.ledger.get_balance("alice"), 100000 - 50500)
        self.assertEqual(self.ledger.account_statement("alice")[0]["status"], "SETTLED")

        with self.assertRaises(KeyError):
            self.ledger.reverse_transfer("nonexistent_tx")

    def test_total_collected_fees_by_currency_and_reversal_exclusion(self) -> None:
        self.ledger.open_account("alice_u", "USD", 500000)
        self.ledger.open_account("bob_u", "USD", 50000)
        self.ledger.open_account("alice_e", "EUR", 200000)
        self.ledger.open_account("bob_e", "EUR", 20000)

        # USD settled: 50000 -> fee 500
        self.ledger.post_transfer("u1", "alice_u", "bob_u", 50000, 100)
        # USD awaiting clearing: 100000 -> fee 500
        self.ledger.post_transfer("u2", "alice_u", "bob_u", 100000, 200)
        # EUR settled: 20000 -> fee 200
        self.ledger.post_transfer("e1", "alice_e", "bob_e", 20000, 300)

        self.assertEqual(self.ledger.total_collected_fees("USD"), 1000)
        self.assertEqual(self.ledger.total_collected_fees("EUR"), 200)
        self.assertEqual(self.ledger.total_collected_fees("GBP"), 0)

        # Reverse u2 -> USD collected fees drop from 1000 to 500
        self.ledger.reverse_transfer("u2")
        self.assertEqual(self.ledger.total_collected_fees("USD"), 500)

        # Reverse u1 -> USD collected fees drop to 0
        self.ledger.reverse_transfer("u1")
        self.assertEqual(self.ledger.total_collected_fees("USD"), 0)
        self.assertEqual(self.ledger.total_collected_fees("EUR"), 200)

    def test_post_transfer_error_contracts_and_no_overdraft(self) -> None:
        self.ledger.open_account("alice", "USD", 10000)
        self.ledger.open_account("bob", "USD", 5000)
        self.ledger.open_account("hans", "EUR", 10000)

        with self.assertRaises(KeyError):
            self.ledger.post_transfer("tx_u1", "ghost", "bob", 100, 1700000000)
        with self.assertRaises(KeyError):
            self.ledger.post_transfer("tx_u2", "alice", "ghost", 100, 1700000000)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_same", "alice", "alice", 100, 1700000000)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_zero", "alice", "bob", 0, 1700000000)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_neg", "alice", "bob", -500, 1700000000)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_fx", "alice", "hans", 100, 1700000000)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer("tx_insuff", "alice", "bob", 10000, 1700000000)


if __name__ == "__main__":
    unittest.main()
