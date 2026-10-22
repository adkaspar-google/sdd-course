"""Comprehensive Clean-Room Verification Suite for LedgerFlow (Milestones 1-4)."""

import unittest
from ledger_flow import LedgerFlow


class TestLedgerFlowCleanRoomRebuild(unittest.TestCase):
  """Verifies all active requirements in SPEC.md and openspec/specs/ledger-flow/spec.md."""

  def setUp(self) -> None:
    self.ledger = LedgerFlow()

  def test_open_account_and_get_balance(self) -> None:
    acct = self.ledger.open_account('  alice  ', 'USD', 250000)
    self.assertEqual(acct['account_id'], 'alice')
    self.assertEqual(acct['currency'], 'USD')
    self.assertEqual(acct['balance'], 250000)
    self.assertEqual(acct['balance_cents'], 250000)
    self.assertEqual(acct['initial_cents'], 250000)
    self.assertEqual(self.ledger.get_balance('alice'), 250000)

    # Mutating returned dict does not mutate internal state
    acct['balance'] = 0
    self.assertEqual(self.ledger.get_balance('alice'), 250000)

  def test_open_account_validation_errors(self) -> None:
    self.ledger.open_account('alice', 'USD', 100)
    with self.assertRaises(ValueError):
      self.ledger.open_account('', 'USD', 0)
    with self.assertRaises(ValueError):
      self.ledger.open_account('   ', 'USD', 0)
    with self.assertRaises(ValueError):
      self.ledger.open_account('alice', 'USD', 50)
    with self.assertRaises(ValueError):
      self.ledger.open_account('  alice ', 'USD', 50)
    with self.assertRaises(ValueError):
      self.ledger.open_account('bob', 'JPY', 0)
    with self.assertRaises(ValueError):
      self.ledger.open_account('bob', 'usd', 0)
    with self.assertRaises(ValueError):
      self.ledger.open_account('bob', 'USD', -1)
    with self.assertRaises(ValueError):
      self.ledger.open_account('bob', 'USD', True)
    with self.assertRaises(KeyError):
      self.ledger.get_balance('unknown')

  def test_post_transfer_standard_and_minimum_fee_floor(self) -> None:
    self.ledger.open_account('alice', 'USD', 100000)
    self.ledger.open_account('bob', 'USD', 0)

    # 500 cents -> 1% is 5, floored to 10 cents
    tx_small = self.ledger.post_transfer('tx_small', 'alice', 'bob', 500, 1700000001)
    self.assertEqual(tx_small['fee_cents'], 10)
    self.assertEqual(tx_small['total_debit_cents'], 510)
    self.assertEqual(tx_small['status'], 'SETTLED')
    self.assertEqual(self.ledger.get_balance('alice'), 100000 - 510)
    self.assertEqual(self.ledger.get_balance('bob'), 500)

    # 50,000 cents -> 100 bps = 500 cents fee, immediate SETTLED
    tx_std = self.ledger.post_transfer('tx_std', 'alice', 'bob', 50000, 1700000002)
    self.assertEqual(tx_std['fee_cents'], 500)
    self.assertEqual(tx_std['total_debit_cents'], 50500)
    self.assertEqual(tx_std['status'], 'SETTLED')
    self.assertEqual(self.ledger.get_balance('alice'), 100000 - 510 - 50500)
    self.assertEqual(self.ledger.get_balance('bob'), 50500)

  def test_post_transfer_high_value_inclusive_100k_and_clearing(self) -> None:
    self.ledger.open_account('alice', 'EUR', 300000)
    self.ledger.open_account('bob', 'EUR', 1000)

    # Exactly 100,000 cents -> 50 bps = 500 cents fee, AWAITING_CLEARING
    tx_100k = self.ledger.post_transfer('tx_100k', 'alice', 'bob', 100000, 1700000010)
    self.assertEqual(tx_100k['fee_cents'], 500)
    self.assertEqual(tx_100k['total_debit_cents'], 100500)
    self.assertEqual(tx_100k['status'], 'AWAITING_CLEARING')
    self.assertEqual(self.ledger.get_balance('alice'), 199500)
    self.assertEqual(self.ledger.get_balance('bob'), 1000)

    # Clear via clear_transfer
    cleared = self.ledger.clear_transfer('tx_100k')
    self.assertEqual(cleared['status'], 'SETTLED')
    self.assertEqual(self.ledger.get_balance('bob'), 101000)

    # Re-clearing raises ValueError
    with self.assertRaises(ValueError):
      self.ledger.clear_transfer('tx_100k')

    # Alias settle_pending works identically
    tx_150k = self.ledger.post_transfer('tx_150k', 'alice', 'bob', 150000, 1700000020)
    self.assertEqual(tx_150k['fee_cents'], 750)
    self.assertEqual(tx_150k['status'], 'AWAITING_CLEARING')
    settled = self.ledger.settle_pending('tx_150k')
    self.assertEqual(settled['status'], 'SETTLED')
    self.assertEqual(self.ledger.get_balance('bob'), 251000)

    with self.assertRaises(KeyError):
      self.ledger.clear_transfer('unknown_tx')

  def test_idempotency_and_conflicting_tx_id(self) -> None:
    self.ledger.open_account('alice', 'GBP', 100000)
    self.ledger.open_account('bob', 'GBP', 0)

    tx1 = self.ledger.post_transfer('tx_idem', 'alice', 'bob', 20000, 1700000000)
    tx2 = self.ledger.post_transfer('tx_idem', 'alice', 'bob', 20000, 1700000999)
    self.assertEqual(tx1, tx2)
    self.assertEqual(self.ledger.get_balance('alice'), 100000 - 20200)
    self.assertEqual(self.ledger.get_balance('bob'), 20000)

    with self.assertRaisesRegex(ValueError, 'Conflicting tx_id'):
      self.ledger.post_transfer('tx_idem', 'alice', 'bob', 25000, 1700000000)
    with self.assertRaisesRegex(ValueError, 'Conflicting tx_id'):
      self.ledger.post_transfer('tx_idem', 'bob', 'alice', 20000, 1700000000)

  def test_overdraft_prohibition_and_validation(self) -> None:
    self.ledger.open_account('alice', 'USD', 1000)
    self.ledger.open_account('bob', 'USD', 0)
    self.ledger.open_account('euro_acct', 'EUR', 1000)

    # 1000 cents requires 1000 + 10 = 1010 cents -> overdraft prohibited
    with self.assertRaises(ValueError):
      self.ledger.post_transfer('tx_over', 'alice', 'bob', 1000, 1700000000)
    self.assertEqual(self.ledger.get_balance('alice'), 1000)

    with self.assertRaises(ValueError):
      self.ledger.post_transfer('tx_same', 'alice', 'alice', 100, 1700000000)
    with self.assertRaises(ValueError):
      self.ledger.post_transfer('tx_zero', 'alice', 'bob', 0, 1700000000)
    with self.assertRaises(ValueError):
      self.ledger.post_transfer('tx_neg', 'alice', 'bob', -100, 1700000000)
    with self.assertRaises(ValueError):
      self.ledger.post_transfer('tx_curr', 'alice', 'euro_acct', 100, 1700000000)
    with self.assertRaises(ValueError):
      self.ledger.post_transfer('', 'alice', 'bob', 100, 1700000000)
    with self.assertRaises(KeyError):
      self.ledger.post_transfer('tx_unk1', 'missing', 'bob', 100, 1700000000)
    with self.assertRaises(KeyError):
      self.ledger.post_transfer('tx_unk2', 'alice', 'missing', 100, 1700000000)

  def test_reverse_transfer_awaiting_clearing_and_settled(self) -> None:
    self.ledger.open_account('alice', 'USD', 300000)
    self.ledger.open_account('bob', 'USD', 0)
    self.ledger.open_account('charlie', 'USD', 0)

    # Reverse AWAITING_CLEARING transfer
    self.ledger.post_transfer('tx_hold', 'alice', 'bob', 100000, 1700000001)
    self.assertEqual(self.ledger.get_balance('alice'), 199500)
    self.assertEqual(self.ledger.get_balance('bob'), 0)
    rev_hold = self.ledger.reverse_transfer('tx_hold')
    self.assertEqual(rev_hold['status'], 'REVERSED')
    self.assertEqual(self.ledger.get_balance('alice'), 300000)
    self.assertEqual(self.ledger.get_balance('bob'), 0)

    # Double reverse fails
    with self.assertRaises(ValueError):
      self.ledger.reverse_transfer('tx_hold')
    # Clearing a reversed transfer fails
    with self.assertRaises(ValueError):
      self.ledger.clear_transfer('tx_hold')

    # Reverse SETTLED transfer when recipient has funds
    self.ledger.post_transfer('tx_settled', 'alice', 'bob', 50000, 1700000002)
    self.assertEqual(self.ledger.get_balance('alice'), 249500)
    self.assertEqual(self.ledger.get_balance('bob'), 50000)
    rev_settled = self.ledger.reverse_transfer('tx_settled')
    self.assertEqual(rev_settled['status'], 'REVERSED')
    self.assertEqual(self.ledger.get_balance('alice'), 300000)
    self.assertEqual(self.ledger.get_balance('bob'), 0)

    # Reverse SETTLED transfer fails if recipient has insufficient funds
    self.ledger.post_transfer('tx_s2', 'alice', 'bob', 50000, 1700000003)
    self.ledger.post_transfer('tx_spend', 'bob', 'charlie', 20000, 1700000004)
    # Bob now has 50000 - 20200 = 29800 < 50000
    with self.assertRaisesRegex(ValueError, 'Recipient has insufficient funds to reverse'):
      self.ledger.reverse_transfer('tx_s2')
    self.assertEqual(self.ledger.get_balance('bob'), 29800)
    self.assertEqual(self.ledger.get_balance('alice'), 249500)

    with self.assertRaises(KeyError):
      self.ledger.reverse_transfer('unknown_tx')

  def test_total_collected_fees(self) -> None:
    self.ledger.open_account('alice', 'USD', 500000)
    self.ledger.open_account('bob', 'USD', 0)
    self.ledger.open_account('eur1', 'EUR', 500000)
    self.ledger.open_account('eur2', 'EUR', 0)

    self.ledger.post_transfer('u1', 'alice', 'bob', 50000, 1700000001)  # fee 500 (SETTLED)
    self.ledger.post_transfer('u2', 'alice', 'bob', 100000, 1700000002)  # fee 500 (AWAITING_CLEARING)
    self.ledger.post_transfer('e1', 'eur1', 'eur2', 20000, 1700000003)  # fee 200 (EUR)

    self.assertEqual(self.ledger.total_collected_fees('USD'), 1000)
    self.assertEqual(self.ledger.total_collected_fees('EUR'), 200)
    self.assertEqual(self.ledger.total_collected_fees('GBP'), 0)

    # Reverse u1 -> fee excluded
    self.ledger.reverse_transfer('u1')
    self.assertEqual(self.ledger.total_collected_fees('USD'), 500)

    # Reverse u2 -> fee excluded
    self.ledger.reverse_transfer('u2')
    self.assertEqual(self.ledger.total_collected_fees('USD'), 0)

    with self.assertRaises(ValueError):
      self.ledger.total_collected_fees('CHF')

  def test_account_statement_ordering_and_defensive_copies(self) -> None:
    self.ledger.open_account('alice', 'USD', 500000)
    self.ledger.open_account('bob', 'USD', 500000)
    self.ledger.open_account('charlie', 'USD', 500000)

    self.ledger.post_transfer('t_late', 'alice', 'bob', 1000, 200)
    self.ledger.post_transfer('t_early_1', 'bob', 'alice', 2000, 100)
    self.ledger.post_transfer('t_early_2', 'alice', 'charlie', 3000, 100)
    self.ledger.post_transfer('t_other', 'bob', 'charlie', 4000, 50)

    stmt = self.ledger.account_statement('alice')
    self.assertEqual([e['tx_id'] for e in stmt], ['t_early_1', 't_early_2', 't_late'])

    # Mutating returned statement does not mutate internal state
    stmt[0]['amount_cents'] = 9999999
    stmt.clear()
    stmt_again = self.ledger.account_statement('alice')
    self.assertEqual(len(stmt_again), 3)
    self.assertEqual(stmt_again[0]['amount_cents'], 2000)

    with self.assertRaises(KeyError):
      self.ledger.account_statement('unknown')


if __name__ == '__main__':
  unittest.main()
