"""Unit tests for clean-room rebuilt LedgerFlow (Milestone 4 SSOT)."""

import unittest
from ledger_flow import LedgerFlow


class TestRebuildPrimary(unittest.TestCase):

    def setUp(self) -> None:
        self.ledger = LedgerFlow()

    def test_ac1_open_account_and_validation(self) -> None:
        acct = self.ledger.open_account('  alice  ', 'USD', 50000)
        self.assertEqual(acct['account_id'], 'alice')
        self.assertEqual(acct['currency'], 'USD')
        self.assertEqual(acct['balance'], 50000)
        self.assertEqual(acct['balance_cents'], 50000)
        self.assertEqual(acct['initial_cents'], 50000)

        with self.assertRaises(ValueError):
            self.ledger.open_account('   ', 'USD', 0)
        with self.assertRaises(ValueError):
            self.ledger.open_account('alice', 'USD', 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account('bob', 'JPY', 100)
        with self.assertRaises(ValueError):
            self.ledger.open_account('bob', 'USD', -1)
        with self.assertRaises(ValueError):
            self.ledger.open_account('bob', 'USD', True)

    def test_ac2_get_balance(self) -> None:
        self.ledger.open_account('alice', 'EUR', 12345)
        self.assertEqual(self.ledger.get_balance('alice'), 12345)
        with self.assertRaises(KeyError):
            self.ledger.get_balance('unknown')

    def test_ac3_and_ac4_post_transfer_fees_and_idempotency(self) -> None:
        self.ledger.open_account('alice', 'USD', 500000)
        self.ledger.open_account('bob', 'USD', 0)
        self.ledger.open_account('eu', 'EUR', 10000)

        # Small transfer (< 1000 cents -> 10 cent floor)
        tx1 = self.ledger.post_transfer('tx1', 'alice', 'bob', 500, 100)
        self.assertEqual(tx1['fee_cents'], 10)
        self.assertEqual(tx1['total_debit_cents'], 510)
        self.assertEqual(tx1['status'], 'SETTLED')
        self.assertEqual(self.ledger.get_balance('alice'), 500000 - 510)
        self.assertEqual(self.ledger.get_balance('bob'), 500)

        # Replay idempotency
        tx1_replay = self.ledger.post_transfer('tx1', 'alice', 'bob', 500, 200)
        self.assertEqual(tx1_replay, tx1)
        self.assertEqual(self.ledger.get_balance('alice'), 500000 - 510)

        # Conflicting tx_id
        with self.assertRaisesRegex(ValueError, 'Conflicting tx_id'):
            self.ledger.post_transfer('tx1', 'alice', 'bob', 600, 200)

        # Standard transfer (< 100,000 cents -> 100 bps)
        tx2 = self.ledger.post_transfer('tx2', 'alice', 'bob', 10000, 105)
        self.assertEqual(tx2['fee_cents'], 100)
        self.assertEqual(tx2['status'], 'SETTLED')

        # High-value transfer (>= 100,000 cents -> 50 bps, AWAITING_CLEARING)
        tx3 = self.ledger.post_transfer('tx3', 'alice', 'bob', 100000, 110)
        self.assertEqual(tx3['fee_cents'], 500)
        self.assertEqual(tx3['status'], 'AWAITING_CLEARING')
        self.assertEqual(self.ledger.get_balance('bob'), 10500)

        # Validation errors
        with self.assertRaises(KeyError):
            self.ledger.post_transfer('tx_u', 'unknown', 'bob', 100, 120)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer('  ', 'alice', 'bob', 100, 120)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer('tx_self', 'alice', 'alice', 100, 120)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer('tx_cur', 'alice', 'eu', 100, 120)
        with self.assertRaises(ValueError):
            self.ledger.post_transfer('tx_over', 'alice', 'bob', 900000, 120)

    def test_ac5_clear_transfer_and_settle_pending_alias(self) -> None:
        self.ledger.open_account('alice', 'USD', 500000)
        self.ledger.open_account('bob', 'USD', 0)

        self.ledger.post_transfer('tx_hold1', 'alice', 'bob', 100000, 10)
        self.ledger.post_transfer('tx_hold2', 'alice', 'bob', 120000, 20)

        cleared1 = self.ledger.clear_transfer('tx_hold1')
        self.assertEqual(cleared1['status'], 'SETTLED')
        self.assertEqual(self.ledger.get_balance('bob'), 100000)

        cleared2 = self.ledger.settle_pending('tx_hold2')
        self.assertEqual(cleared2['status'], 'SETTLED')
        self.assertEqual(self.ledger.get_balance('bob'), 220000)

        with self.assertRaises(ValueError):
            self.ledger.clear_transfer('tx_hold1')
        with self.assertRaises(KeyError):
            self.ledger.clear_transfer('unknown_tx')

    def test_ac6_reverse_transfer(self) -> None:
        self.ledger.open_account('alice', 'USD', 300000)
        self.ledger.open_account('bob', 'USD', 0)
        self.ledger.open_account('charlie', 'USD', 0)

        # Reverse AWAITING_CLEARING
        self.ledger.post_transfer('tx_hold', 'alice', 'bob', 100000, 10)
        self.assertEqual(self.ledger.get_balance('alice'), 199500)
        rev_hold = self.ledger.reverse_transfer('tx_hold')
        self.assertEqual(rev_hold['status'], 'REVERSED')
        self.assertEqual(self.ledger.get_balance('alice'), 300000)
        self.assertEqual(self.ledger.get_balance('bob'), 0)

        # Reverse SETTLED
        self.ledger.post_transfer('tx_set', 'alice', 'bob', 20000, 20)
        self.assertEqual(self.ledger.get_balance('alice'), 300000 - 20200)
        self.assertEqual(self.ledger.get_balance('bob'), 20000)
        rev_set = self.ledger.reverse_transfer('tx_set')
        self.assertEqual(rev_set['status'], 'REVERSED')
        self.assertEqual(self.ledger.get_balance('alice'), 300000)
        self.assertEqual(self.ledger.get_balance('bob'), 0)

        # Double reversal fails
        with self.assertRaises(ValueError):
            self.ledger.reverse_transfer('tx_set')

        # Insufficient recipient funds to reverse SETTLED transfer
        self.ledger.post_transfer('tx_s2', 'alice', 'bob', 10000, 30)
        self.ledger.post_transfer('tx_s3', 'bob', 'charlie', 5000, 40)
        with self.assertRaisesRegex(
            ValueError, 'Recipient has insufficient funds to reverse'
        ):
            self.ledger.reverse_transfer('tx_s2')

    def test_ac7_total_collected_fees(self) -> None:
        self.ledger.open_account('a_usd', 'USD', 500000)
        self.ledger.open_account('b_usd', 'USD', 0)
        self.ledger.open_account('a_eur', 'EUR', 100000)
        self.ledger.open_account('b_eur', 'EUR', 0)

        self.ledger.post_transfer('t1', 'a_usd', 'b_usd', 10000, 10)   # fee 100
        self.ledger.post_transfer('t2', 'a_usd', 'b_usd', 100000, 20)  # fee 500
        self.ledger.post_transfer('t3', 'a_eur', 'b_eur', 5000, 30)    # fee 50
        self.assertEqual(self.ledger.total_collected_fees('USD'), 600)
        self.assertEqual(self.ledger.total_collected_fees('EUR'), 50)
        self.assertEqual(self.ledger.total_collected_fees('GBP'), 0)

        self.ledger.reverse_transfer('t1')
        self.assertEqual(self.ledger.total_collected_fees('USD'), 500)

        with self.assertRaises(ValueError):
            self.ledger.total_collected_fees('CAD')

    def test_ac8_account_statement(self) -> None:
        self.ledger.open_account('alice', 'USD', 100000)
        self.ledger.open_account('bob', 'USD', 100000)

        self.ledger.post_transfer('tx_b', 'alice', 'bob', 1000, 50)
        self.ledger.post_transfer('tx_a', 'bob', 'alice', 2000, 10)
        self.ledger.post_transfer('tx_c', 'alice', 'bob', 3000, 50)

        stmt = self.ledger.account_statement('alice')
        self.assertEqual([e['tx_id'] for e in stmt], ['tx_a', 'tx_b', 'tx_c'])
        stmt[0]['amount_cents'] = 999999
        self.assertEqual(
            self.ledger.account_statement('alice')[0]['amount_cents'], 2000
        )

        with self.assertRaises(KeyError):
            self.ledger.account_statement('missing')


if __name__ == '__main__':
    unittest.main()
