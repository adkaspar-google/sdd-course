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
"""LedgerFlow — Clean-Room Settlement Ledger Engine."""

from typing import Dict, List


class LedgerFlow:
    """In-memory, deterministic settlement ledger engine."""

    SUPPORTED_CURRENCIES = {'USD', 'EUR', 'GBP'}
    HIGH_VALUE_THRESHOLD_CENTS = 100000
    MIN_FEE_CENTS = 10

    def __init__(self) -> None:
        self.accounts: Dict[str, dict] = {}
        self.transactions: Dict[str, dict] = {}
        self._entries: List[dict] = []

    def open_account(
        self,
        account_id: str,
        currency: str = 'USD',
        initial_cents: int = 0,
    ) -> dict:
        """Open a new currency-denominated account with an integer cent balance."""
        if not isinstance(account_id, str) or not account_id.strip():
            raise ValueError('account_id must be a non-empty string')
        clean_id = account_id.strip()
        if clean_id in self.accounts:
            raise ValueError(f'Account already exists: {clean_id}')
        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f'Unsupported currency: {currency}')
        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError('initial_cents must be a non-negative integer')

        record = {
            'account_id': clean_id,
            'currency': currency,
            'balance': initial_cents,
            'balance_cents': initial_cents,
            'initial_cents': initial_cents,
        }
        self.accounts[clean_id] = record
        return dict(record)

    def get_balance(self, account_id: str) -> int:
        """Return the current integer balance in cents for an existing account."""
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        clean_id = account_id.strip()
        if clean_id not in self.accounts:
            raise KeyError(account_id)
        return self.accounts[clean_id]['balance']

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> dict:
        """Execute a same-currency transfer between two distinct accounts."""
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError('tx_id must be a non-empty string')
        clean_tx_id = tx_id.strip()

        if clean_tx_id in self.transactions:
            existing = self.transactions[clean_tx_id]
            clean_from = from_acct.strip() if isinstance(from_acct, str) else from_acct
            clean_to = to_acct.strip() if isinstance(to_acct, str) else to_acct
            if (
                not isinstance(amount_cents, bool)
                and (
                    existing['from_acct'],
                    existing['to_acct'],
                    existing['amount_cents'],
                )
                == (clean_from, clean_to, amount_cents)
            ):
                return dict(existing)
            raise ValueError('Conflicting tx_id')

        if not isinstance(from_acct, str) or from_acct.strip() not in self.accounts:
            raise KeyError(from_acct)
        if not isinstance(to_acct, str) or to_acct.strip() not in self.accounts:
            raise KeyError(to_acct)

        clean_from = from_acct.strip()
        clean_to = to_acct.strip()

        if clean_from == clean_to:
            raise ValueError('Cannot transfer to the same account')

        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError('amount_cents must be a positive integer')

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError('timestamp must be an integer')

        sender = self.accounts[clean_from]
        recipient = self.accounts[clean_to]

        if sender['currency'] != recipient['currency']:
            raise ValueError('Currency mismatch between accounts')

        if amount_cents >= self.HIGH_VALUE_THRESHOLD_CENTS:
            fee_cents = max(self.MIN_FEE_CENTS, (amount_cents * 50) // 10000)
            status = 'AWAITING_CLEARING'
        else:
            fee_cents = max(self.MIN_FEE_CENTS, amount_cents // 100)
            status = 'SETTLED'

        total_debit_cents = amount_cents + fee_cents
        if sender['balance'] < total_debit_cents:
            raise ValueError('Insufficient funds')

        sender['balance'] -= total_debit_cents
        sender['balance_cents'] = sender['balance']

        if status == 'SETTLED':
            recipient['balance'] += amount_cents
            recipient['balance_cents'] = recipient['balance']

        entry = {
            'tx_id': clean_tx_id,
            'from_acct': clean_from,
            'to_acct': clean_to,
            'amount_cents': amount_cents,
            'fee_cents': fee_cents,
            'total_debit_cents': total_debit_cents,
            'currency': sender['currency'],
            'timestamp': timestamp,
            'status': status,
        }
        self.transactions[clean_tx_id] = entry
        self._entries.append(entry)
        return dict(entry)

    def clear_transfer(self, tx_id: str) -> dict:
        """Clear a held AWAITING_CLEARING transfer and credit the recipient."""
        if not isinstance(tx_id, str) or tx_id.strip() not in self.transactions:
            raise KeyError(tx_id)
        clean_tx_id = tx_id.strip()
        entry = self.transactions[clean_tx_id]

        if entry['status'] != 'AWAITING_CLEARING':
            raise ValueError(f"Cannot clear transfer in status {entry['status']}")

        recipient = self.accounts[entry['to_acct']]
        recipient['balance'] += entry['amount_cents']
        recipient['balance_cents'] = recipient['balance']
        entry['status'] = 'SETTLED'
        return dict(entry)

    def settle_pending(self, tx_id: str) -> dict:
        """Backward-compatible alias for clear_transfer."""
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> dict:
        """Reverse an AWAITING_CLEARING or SETTLED transfer with full fee refund."""
        if not isinstance(tx_id, str) or tx_id.strip() not in self.transactions:
            raise KeyError(tx_id)
        clean_tx_id = tx_id.strip()
        entry = self.transactions[clean_tx_id]

        if entry['status'] == 'REVERSED':
            raise ValueError('Transfer is already REVERSED')

        sender = self.accounts[entry['from_acct']]
        recipient = self.accounts[entry['to_acct']]

        if entry['status'] == 'SETTLED':
            if recipient['balance'] < entry['amount_cents']:
                raise ValueError('Recipient has insufficient funds to reverse')
            recipient['balance'] -= entry['amount_cents']
            recipient['balance_cents'] = recipient['balance']
            sender['balance'] += entry['amount_cents'] + entry['fee_cents']
            sender['balance_cents'] = sender['balance']
            entry['status'] = 'REVERSED'
            return dict(entry)

        if entry['status'] == 'AWAITING_CLEARING':
            sender['balance'] += entry['amount_cents'] + entry['fee_cents']
            sender['balance_cents'] = sender['balance']
            entry['status'] = 'REVERSED'
            return dict(entry)

        raise ValueError(f"Cannot reverse transfer in status {entry['status']}")

    def total_collected_fees(self, currency: str = 'USD') -> int:
        """Return total collected platform fees across non-reversed transfers in currency."""
        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f'Unsupported currency: {currency}')
        return sum(
            entry['fee_cents']
            for entry in self._entries
            if entry['currency'] == currency
            and entry['status'] in ('SETTLED', 'AWAITING_CLEARING')
        )

    def account_statement(self, account_id: str) -> List[dict]:
        """Return chronological list of transfer copies involving account_id."""
        if not isinstance(account_id, str) or account_id.strip() not in self.accounts:
            raise KeyError(account_id)
        clean_id = account_id.strip()

        indexed = [
            (idx, entry)
            for idx, entry in enumerate(self._entries)
            if entry['from_acct'] == clean_id or entry['to_acct'] == clean_id
        ]
        indexed.sort(key=lambda item: (item[1]['timestamp'], item[0]))
        return [dict(entry) for _, entry in indexed]
