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
"""LedgerFlow implementation from Milestone 1 specification."""

from typing import Any, Dict


class LedgerFlow:
    """Core multi-currency ledger supporting account creation, balance inquiry, and single-currency transfers."""

    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}
    PENDING_THRESHOLD_CENTS = 100000

    def __init__(self) -> None:
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> Dict[str, Any]:
        """Opens a new ledger account."""
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        cleaned_id = account_id.strip()
        if not cleaned_id:
            raise ValueError("account_id must be a non-empty string")
        if cleaned_id in self.accounts:
            raise ValueError(f"Duplicate account_id: {cleaned_id}")

        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Invalid currency: {currency}")

        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be an integer >= 0")

        record = {
            "account_id": cleaned_id,
            "currency": currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
        }
        self.accounts[cleaned_id] = record
        return dict(record)

    def get_balance(self, account_id: str) -> int:
        """Returns the current integer balance in cents for account_id."""
        if account_id not in self.accounts:
            raise KeyError(f"Unknown account_id: {account_id}")
        return self.accounts[account_id]["balance_cents"]

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> Dict[str, Any]:
        """Executes a single-currency transfer with a flat 1% platform fee."""
        if from_acct not in self.accounts:
            raise KeyError(f"Unknown from_acct: {from_acct}")
        if to_acct not in self.accounts:
            raise KeyError(f"Unknown to_acct: {to_acct}")

        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string")
        cleaned_tx_id = tx_id.strip()
        if cleaned_tx_id in self.transactions:
            raise ValueError(f"Duplicate tx_id: {cleaned_tx_id}")

        if from_acct == to_acct:
            raise ValueError("from_acct and to_acct must be different")

        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        sender = self.accounts[from_acct]
        receiver = self.accounts[to_acct]

        if sender["currency"] != receiver["currency"]:
            raise ValueError("Currency mismatch between from_acct and to_acct")

        fee_cents = amount_cents // 100
        total_debit = amount_cents + fee_cents

        if sender["balance_cents"] < total_debit:
            raise ValueError("Insufficient funds")

        sender["balance_cents"] -= total_debit
        sender["balance"] = sender["balance_cents"]

        if amount_cents > self.PENDING_THRESHOLD_CENTS:
            status = "PENDING"
        else:
            status = "SETTLED"
            receiver["balance_cents"] += amount_cents
            receiver["balance"] = receiver["balance_cents"]

        tx_record = {
            "tx_id": cleaned_tx_id,
            "from_acct": from_acct,
            "to_acct": to_acct,
            "amount_cents": amount_cents,
            "amount": amount_cents,
            "fee_cents": fee_cents,
            "fee": fee_cents,
            "total_debit_cents": total_debit,
            "currency": sender["currency"],
            "timestamp": timestamp,
            "status": status,
        }
        self.transactions[cleaned_tx_id] = tx_record
        return dict(tx_record)
