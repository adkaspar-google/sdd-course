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
"""Clean-room implementation of LedgerFlow from M1-M4 specification documents."""

from typing import Any


class LedgerFlow:
    """Multi-currency ledger with tiered fees, clearing, idempotency, and reversals."""

    SUPPORTED_CURRENCIES = frozenset({"USD", "EUR", "GBP"})
    CLEARING_THRESHOLD_CENTS = 100_000
    MIN_FEE_CENTS = 10

    def __init__(self) -> None:
        self._accounts: dict[str, dict[str, Any]] = {}
        self._transactions: dict[str, dict[str, Any]] = {}
        self._tx_order: dict[str, int] = {}
        self._next_index: int = 0

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> dict[str, Any]:
        """Opens a new ledger account with an initial integer balance in cents."""
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        cleaned_id = account_id.strip()
        if not cleaned_id:
            raise ValueError("account_id must be non-empty")
        if cleaned_id in self._accounts:
            raise ValueError(f"Duplicate account_id: {cleaned_id}")

        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        if (
            isinstance(initial_cents, bool)
            or not isinstance(initial_cents, int)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be an integer >= 0")

        account = {
            "account_id": cleaned_id,
            "currency": currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
        }
        self._accounts[cleaned_id] = account
        return dict(account)

    def get_balance(self, account_id: str) -> int:
        """Returns the current integer balance in cents for account_id."""
        if account_id not in self._accounts:
            raise KeyError(f"Unknown account_id: {account_id}")
        return self._accounts[account_id]["balance_cents"]

    def _set_balance(self, account_id: str, new_balance_cents: int) -> None:
        acct = self._accounts[account_id]
        acct["balance"] = new_balance_cents
        acct["balance_cents"] = new_balance_cents

    @classmethod
    def _calculate_fee(cls, amount_cents: int) -> int:
        if amount_cents >= cls.CLEARING_THRESHOLD_CENTS:
            return max(cls.MIN_FEE_CENTS, (amount_cents * 50) // 10_000)
        return max(cls.MIN_FEE_CENTS, amount_cents // 100)

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> dict[str, Any]:
        """Posts a single-currency transfer with replay-safe idempotency and tiered fees."""
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string")
        cleaned_tx_id = tx_id.strip()

        if cleaned_tx_id in self._transactions:
            existing = self._transactions[cleaned_tx_id]
            if (
                existing["from_acct"] == from_acct
                and existing["to_acct"] == to_acct
                and existing["amount_cents"] == amount_cents
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        if from_acct not in self._accounts:
            raise KeyError(f"Unknown from_acct: {from_acct}")
        if to_acct not in self._accounts:
            raise KeyError(f"Unknown to_acct: {to_acct}")

        if from_acct == to_acct:
            raise ValueError("from_acct and to_acct must be different")

        if (
            isinstance(amount_cents, bool)
            or not isinstance(amount_cents, int)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")

        if isinstance(timestamp, bool) or not isinstance(timestamp, int):
            raise ValueError("timestamp must be an integer")

        sender = self._accounts[from_acct]
        recipient = self._accounts[to_acct]
        if sender["currency"] != recipient["currency"]:
            raise ValueError("Currency mismatch between accounts")

        fee_cents = self._calculate_fee(amount_cents)
        total_debit = amount_cents + fee_cents
        if sender["balance_cents"] < total_debit:
            raise ValueError("Insufficient funds")

        self._set_balance(from_acct, sender["balance_cents"] - total_debit)

        if amount_cents >= self.CLEARING_THRESHOLD_CENTS:
            status = "AWAITING_CLEARING"
        else:
            status = "SETTLED"
            self._set_balance(to_acct, recipient["balance_cents"] + amount_cents)

        tx = {
            "tx_id": cleaned_tx_id,
            "from_acct": from_acct,
            "to_acct": to_acct,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "currency": sender["currency"],
            "timestamp": timestamp,
            "status": status,
        }
        self._transactions[cleaned_tx_id] = tx
        self._tx_order[cleaned_tx_id] = self._next_index
        self._next_index += 1
        return dict(tx)

    def clear_transfer(self, tx_id: str) -> dict[str, Any]:
        """Transitions an AWAITING_CLEARING transfer to SETTLED and credits recipient."""
        if tx_id not in self._transactions:
            raise KeyError(f"Unknown tx_id: {tx_id}")
        tx = self._transactions[tx_id]
        if tx["status"] != "AWAITING_CLEARING":
            raise ValueError(
                f"Transfer {tx_id} cannot be cleared from status {tx['status']}"
            )

        to_acct = tx["to_acct"]
        recipient = self._accounts[to_acct]
        self._set_balance(to_acct, recipient["balance_cents"] + tx["amount_cents"])
        tx["status"] = "SETTLED"
        return dict(tx)

    def settle_pending(self, tx_id: str) -> dict[str, Any]:
        """Backward-compatible alias for clear_transfer."""
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> dict[str, Any]:
        """Reverses an AWAITING_CLEARING or SETTLED transfer and refunds fees."""
        if tx_id not in self._transactions:
            raise KeyError(f"Unknown tx_id: {tx_id}")
        tx = self._transactions[tx_id]
        status = tx["status"]
        if status == "REVERSED":
            raise ValueError(f"Transfer {tx_id} is already REVERSED")

        from_acct = tx["from_acct"]
        to_acct = tx["to_acct"]
        amount_cents = tx["amount_cents"]
        fee_cents = tx["fee_cents"]

        if status == "AWAITING_CLEARING":
            sender = self._accounts[from_acct]
            self._set_balance(
                from_acct, sender["balance_cents"] + amount_cents + fee_cents
            )
            tx["status"] = "REVERSED"
            return dict(tx)

        if status == "SETTLED":
            recipient = self._accounts[to_acct]
            if recipient["balance_cents"] < amount_cents:
                raise ValueError("Recipient has insufficient funds to reverse")
            sender = self._accounts[from_acct]
            self._set_balance(to_acct, recipient["balance_cents"] - amount_cents)
            self._set_balance(
                from_acct, sender["balance_cents"] + amount_cents + fee_cents
            )
            tx["status"] = "REVERSED"
            return dict(tx)

        raise ValueError(f"Unsupported transfer status for reversal: {status}")

    def account_statement(self, account_id: str) -> list[dict[str, Any]]:
        """Returns chronological shallow copies of transfers involving account_id."""
        if account_id not in self._accounts:
            raise KeyError(f"Unknown account_id: {account_id}")

        matching = [
            tx
            for tx in self._transactions.values()
            if tx["from_acct"] == account_id or tx["to_acct"] == account_id
        ]
        matching.sort(key=lambda tx: (tx["timestamp"], self._tx_order[tx["tx_id"]]))
        return [dict(tx) for tx in matching]

    def total_collected_fees(self, currency: str = "USD") -> int:
        """Sums fee_cents for all non-reversed transfers in the given currency."""
        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        return sum(
            tx["fee_cents"]
            for tx in self._transactions.values()
            if tx["currency"] == currency
            and tx["status"] in ("SETTLED", "AWAITING_CLEARING")
        )
