"""Verification unit tests for clean-room rebuilt LedgerFlow."""

import unittest
from ledger_flow import LedgerFlow


class TestRebuildLedgerFlow(unittest.TestCase):
    """Comprehensive verification suite across Milestones 1 through 4."""

    def test_open_account_and_get_balance(self) -> None:
        ledger = LedgerFlow()
        acct = ledger.open_account("  alice  ", "USD", 50_000)
        self.assertEqual(acct["account_id"], "alice")
        self.assertEqual(acct["currency"], "USD")
        self.assertEqual(acct["balance"], 50_000)
        self.assertEqual(acct["balance_cents"], 50_000)
        self.assertEqual(ledger.get_balance("alice"), 50_000)
        self.assertEqual(ledger.get_balance("  alice "), 50_000)

        for invalid_id in ["", "   "]:
            with self.assertRaises(ValueError):
                ledger.open_account(invalid_id, "USD", 0)
        with self.assertRaises(ValueError):
            ledger.open_account("alice", "USD", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "usd", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "JPY", 100)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "USD", -1)
        with self.assertRaises(ValueError):
            ledger.open_account("bob", "USD", True)
        with self.assertRaises(KeyError):
            ledger.get_balance("unknown")

    def test_post_transfer_tiered_fees_and_thresholds(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("alice", "USD", 500_000)
        ledger.open_account("bob", "USD", 0)

        # Small transfer (< 1000 cents): 10-cent minimum floor applies
        tx1 = ledger.post_transfer("tx1", "alice", "bob", 500, 100)
        self.assertEqual(tx1["fee_cents"], 10)
        self.assertEqual(tx1["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("alice"), 500_000 - 510)
        self.assertEqual(ledger.get_balance("bob"), 500)

        # Standard transfer (< 100_000 cents): 1% fee (99_999 // 100 = 999)
        tx2 = ledger.post_transfer("tx2", "alice", "bob", 99_999, 200)
        self.assertEqual(tx2["fee_cents"], 999)
        self.assertEqual(tx2["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("bob"), 100_499)

        # High-value transfer at boundary (100_000 cents): 50 bps fee = 500, AWAITING_CLEARING
        tx3 = ledger.post_transfer("tx3", "alice", "bob", 100_000, 150)
        self.assertEqual(tx3["fee_cents"], 500)
        self.assertEqual(tx3["status"], "AWAITING_CLEARING")
        self.assertEqual(ledger.get_balance("bob"), 100_499)

    def test_idempotency_and_conflicts(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("alice", "EUR", 200_000)
        ledger.open_account("bob", "EUR", 10_000)

        tx = ledger.post_transfer("tx-idem", "alice", "bob", 10_000, 10)
        bal_alice = ledger.get_balance("alice")
        bal_bob = ledger.get_balance("bob")

        replay = ledger.post_transfer("tx-idem", "alice", "bob", 10_000, 999)
        self.assertEqual(replay, tx)
        self.assertEqual(ledger.get_balance("alice"), bal_alice)
        self.assertEqual(ledger.get_balance("bob"), bal_bob)
        self.assertEqual(len(ledger.account_statement("alice")), 1)

        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-idem", "alice", "bob", 20_000, 10)
        with self.assertRaises(ValueError):
            ledger.post_transfer("tx-idem", "bob", "alice", 10_000, 10)

    def test_clearing_and_statements(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("a", "GBP", 500_000)
        ledger.open_account("b", "GBP", 0)

        ledger.post_transfer("t1", "a", "b", 100_000, 30)
        ledger.post_transfer("t2", "a", "b", 5_000, 10)
        ledger.post_transfer("t3", "a", "b", 120_000, 10)

        cleared = ledger.clear_transfer("t1")
        self.assertEqual(cleared["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("b"), 105_000)

        cleared2 = ledger.settle_pending("t3")
        self.assertEqual(cleared2["status"], "SETTLED")
        self.assertEqual(ledger.get_balance("b"), 225_000)

        with self.assertRaises(ValueError):
            ledger.clear_transfer("t1")
        with self.assertRaises(KeyError):
            ledger.clear_transfer("unknown-tx")

        stmt = ledger.account_statement("a")
        self.assertEqual([e["tx_id"] for e in stmt], ["t2", "t3", "t1"])
        stmt[0]["status"] = "MUTATED"
        self.assertEqual(ledger.account_statement("a")[0]["status"], "SETTLED")

    def test_reversals_and_collected_fees(self) -> None:
        ledger = LedgerFlow()
        ledger.open_account("sender", "USD", 500_000)
        ledger.open_account("recipient", "USD", 0)
        ledger.open_account("third", "USD", 0)

        # Transfer 1: settled (10_000, fee 100)
        ledger.post_transfer("tx_settled", "sender", "recipient", 10_000, 1)
        # Transfer 2: awaiting clearing (100_000, fee 500)
        ledger.post_transfer("tx_awaiting", "sender", "recipient", 100_000, 2)

        self.assertEqual(ledger.total_collected_fees("USD"), 600)

        # Reverse awaiting clearing transfer -> refunds 100_500 to sender, recipient untouched
        rev_awaiting = ledger.reverse_transfer("tx_awaiting")
        self.assertEqual(rev_awaiting["status"], "REVERSED")
        self.assertEqual(ledger.get_balance("sender"), 500_000 - 10_100)
        self.assertEqual(ledger.get_balance("recipient"), 10_000)
        self.assertEqual(ledger.total_collected_fees("USD"), 100)

        # Clearing a reversed transfer must fail with ValueError
        with self.assertRaises(ValueError):
            ledger.clear_transfer("tx_awaiting")

        # Reverse settled transfer -> debits 10_000 from recipient, refunds 10_100 to sender
        rev_settled = ledger.reverse_transfer("tx_settled")
        self.assertEqual(rev_settled["status"], "REVERSED")
        self.assertEqual(ledger.get_balance("sender"), 500_000)
        self.assertEqual(ledger.get_balance("recipient"), 0)
        self.assertEqual(ledger.total_collected_fees("USD"), 0)

        # Reversing again raises ValueError
        with self.assertRaises(ValueError):
            ledger.reverse_transfer("tx_settled")

        # Insufficient recipient funds to reverse
        ledger.post_transfer("tx_drain", "sender", "recipient", 10_000, 3)
        ledger.post_transfer("tx_move", "recipient", "third", 5_000, 4)
        with self.assertRaises(ValueError):
            ledger.reverse_transfer("tx_drain")

        with self.assertRaises(ValueError):
            ledger.total_collected_fees("CAD")


if __name__ == "__main__":
    unittest.main()
