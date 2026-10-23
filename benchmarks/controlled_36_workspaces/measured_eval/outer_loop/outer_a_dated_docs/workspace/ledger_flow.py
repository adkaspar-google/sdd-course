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
"""Outer-Loop M1->M5 Continuous Evolution: LedgerFlow."""

from typing import Any, Dict, List


SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}
CLEARING_THRESHOLD_CENTS = 100000
MIN_FEE_CENTS = 10


class LedgerFlow:
    """Multi-milestone settlement ledger."""

    def __init__(self) -> None:
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.entries: List[Dict[str, Any]] = []
        self.transactions: Dict[str, Dict[str, Any]] = {}

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> Dict[str, Any]:
        """Creates an account with trimmed non-empty account_id, valid currency, and initial_cents >= 0."""
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        clean_id = account_id.strip()
        if not clean_id:
            raise ValueError("account_id must be non-empty")
        if clean_id in self.accounts:
            raise ValueError(f"Duplicate account_id: {clean_id}")

        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        clean_currency = currency.strip().upper()
        if clean_currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be an integer >= 0")

        account = {
            "account_id": clean_id,
            "currency": clean_currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
        }
        self.accounts[clean_id] = account
        return dict(account)

    def get_balance(self, account_id: str) -> int:
        """Returns current integer balance in cents (raises KeyError if unknown)."""
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        clean_id = account_id.strip()
        if clean_id not in self.accounts:
            raise KeyError(account_id)
        return int(self.accounts[clean_id]["balance"])

    @staticmethod
    def _calculate_fee(amount_cents: int) -> int:
        """Calculates tiered platform fee with a 10-cent minimum floor."""
        if amount_cents >= CLEARING_THRESHOLD_CENTS:
            return max(MIN_FEE_CENTS, (amount_cents * 50) // 10000)
        return max(MIN_FEE_CENTS, amount_cents // 100)

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> Dict[str, Any]:
        """Transfers amount_cents > 0 between two distinct existing accounts of the same currency."""
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string")
        clean_tx_id = tx_id.strip()

        from_id = from_acct.strip() if isinstance(from_acct, str) else ""
        to_id = to_acct.strip() if isinstance(to_acct, str) else ""

        if clean_tx_id in self.transactions:
            existing = self.transactions[clean_tx_id]
            if (
                existing["from_acct"] == from_id
                and existing["to_acct"] == to_id
                and existing["amount_cents"] == amount_cents
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        if not isinstance(from_acct, str) or not isinstance(to_acct, str):
            raise KeyError("Account IDs must be strings")

        if from_id not in self.accounts:
            raise KeyError(from_acct)
        if to_id not in self.accounts:
            raise KeyError(to_acct)

        if from_id == to_id:
            raise ValueError("Cannot transfer to the same account")

        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")

        sender = self.accounts[from_id]
        receiver = self.accounts[to_id]

        if sender["currency"] != receiver["currency"]:
            raise ValueError("Currency mismatch between accounts")

        fee_cents = self._calculate_fee(amount_cents)
        total_debit = amount_cents + fee_cents

        if sender["balance"] < total_debit:
            raise ValueError("Insufficient funds")

        sender["balance"] -= total_debit
        sender["balance_cents"] = sender["balance"]

        if amount_cents >= CLEARING_THRESHOLD_CENTS:
            status = "AWAITING_CLEARING"
        else:
            status = "SETTLED"
            receiver["balance"] += amount_cents
            receiver["balance_cents"] = receiver["balance"]

        tx = {
            "tx_id": clean_tx_id,
            "from_acct": from_id,
            "to_acct": to_id,
            "currency": sender["currency"],
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "total_debit_cents": total_debit,
            "timestamp": timestamp,
            "status": status,
        }
        self.entries.append(tx)
        self.transactions[clean_tx_id] = tx
        return dict(tx)

    def clear_transfer(self, tx_id: str) -> Dict[str, Any]:
        """Transitions an 'AWAITING_CLEARING' transfer to 'SETTLED' and credits amount_cents to to_acct."""
        if not isinstance(tx_id, str):
            raise KeyError(tx_id)
        clean_tx_id = tx_id.strip()
        if clean_tx_id not in self.transactions:
            raise KeyError(tx_id)

        tx = self.transactions[clean_tx_id]
        if tx["status"] != "AWAITING_CLEARING":
            raise ValueError(
                f"Transaction {clean_tx_id} is not in AWAITING_CLEARING state"
            )

        tx["status"] = "SETTLED"
        receiver = self.accounts[tx["to_acct"]]
        receiver["balance"] += tx["amount_cents"]
        receiver["balance_cents"] = receiver["balance"]
        return dict(tx)

    def settle_pending(self, tx_id: str) -> Dict[str, Any]:
        """Backward-compatible alias that delegates to clear_transfer(tx_id)."""
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> Dict[str, Any]:
        """Reverses an AWAITING_CLEARING or SETTLED transfer and refunds amount_cents + fee_cents to from_acct."""
        if not isinstance(tx_id, str):
            raise KeyError(tx_id)
        clean_tx_id = tx_id.strip()
        if clean_tx_id not in self.transactions:
            raise KeyError(tx_id)

        tx = self.transactions[clean_tx_id]
        if tx["status"] == "REVERSED":
            raise ValueError(f"Transaction {clean_tx_id} is already REVERSED")

        sender = self.accounts[tx["from_acct"]]
        receiver = self.accounts[tx["to_acct"]]
        amount_cents = tx["amount_cents"]
        fee_cents = tx["fee_cents"]

        if tx["status"] == "AWAITING_CLEARING":
            sender["balance"] += amount_cents + fee_cents
            sender["balance_cents"] = sender["balance"]
            tx["status"] = "REVERSED"
        elif tx["status"] == "SETTLED":
            if receiver["balance"] < amount_cents:
                raise ValueError("Recipient has insufficient funds to reverse")
            receiver["balance"] -= amount_cents
            receiver["balance_cents"] = receiver["balance"]
            sender["balance"] += amount_cents + fee_cents
            sender["balance_cents"] = sender["balance"]
            tx["status"] = "REVERSED"
        else:
            raise ValueError(f"Cannot reverse transaction in state {tx['status']}")

        return dict(tx)

    def total_collected_fees(self, currency: str = "USD") -> int:
        """Returns the sum of fee_cents across all non-reversed transfers in the given currency."""
        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        clean_currency = currency.strip().upper()
        if clean_currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        return sum(
            tx["fee_cents"]
            for tx in self.entries
            if tx["currency"] == clean_currency
            and tx["status"] in ("SETTLED", "AWAITING_CLEARING")
        )

    def account_statement(self, account_id: str) -> List[Dict[str, Any]]:
        """Returns copies of all transfers involving account_id sorted by (timestamp, insertion_index) ascending."""
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        clean_id = account_id.strip()
        if clean_id not in self.accounts:
            raise KeyError(account_id)

        matching = [
            (idx, tx)
            for idx, tx in enumerate(self.entries)
            if tx["from_acct"] == clean_id or tx["to_acct"] == clean_id
        ]
        matching.sort(key=lambda pair: (pair[1]["timestamp"], pair[0]))
        return [dict(tx) for _, tx in matching]
