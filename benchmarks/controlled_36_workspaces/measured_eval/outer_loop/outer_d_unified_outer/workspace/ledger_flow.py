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
"""Outer-Loop M1->M5 Continuous Evolution: LedgerFlow (Milestone 4 — Reversals & Constitutional Scope Governance)."""

from typing import Any, Dict, List


VALID_CURRENCIES = frozenset({"USD", "EUR", "GBP"})
HIGH_VALUE_THRESHOLD_CENTS = 100000
MIN_FEE_CENTS = 10


class LedgerFlow:
    """Multi-milestone settlement ledger."""

    def __init__(self) -> None:
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.entries: List[Dict[str, Any]] = []

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> Dict[str, Any]:
        """Creates an account with trimmed non-empty account_id, uppercase 3-letter currency, and initial_cents >= 0."""
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        clean_id = account_id.strip()
        if not clean_id:
            raise ValueError("account_id must be a non-empty string")
        if clean_id in self.accounts:
            raise ValueError(f"Duplicate account_id: {clean_id}")

        if not isinstance(currency, str) or currency not in VALID_CURRENCIES:
            raise ValueError(f"Invalid currency: {currency!r}. Must be one of {sorted(VALID_CURRENCIES)}")

        if not isinstance(initial_cents, int) or isinstance(initial_cents, bool) or initial_cents < 0:
            raise ValueError("initial_cents must be an integer >= 0")

        account_record: Dict[str, Any] = {
            "account_id": clean_id,
            "currency": currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
            "initial_cents": initial_cents,
        }
        self.accounts[clean_id] = account_record
        return dict(account_record)

    def get_balance(self, account_id: str) -> int:
        """Returns current integer balance in cents (raises KeyError if unknown)."""
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        clean_id = account_id.strip()
        if not clean_id or clean_id not in self.accounts:
            raise KeyError(account_id)
        return int(self.accounts[clean_id]["balance"])

    @staticmethod
    def _calculate_fee(amount_cents: int) -> int:
        """Calculates tiered platform fee with a 10-cent minimum floor."""
        if amount_cents >= HIGH_VALUE_THRESHOLD_CENTS:
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
        """Posts a replay-safe same-currency transfer with tiered fee and >= 100,000 awaiting-clearing hold."""
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
                and not isinstance(amount_cents, bool)
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        if not from_id or from_id not in self.accounts:
            raise KeyError(from_acct)
        if not to_id or to_id not in self.accounts:
            raise KeyError(to_acct)

        if from_id == to_id:
            raise ValueError("from_acct and to_acct must be distinct accounts")

        if not isinstance(amount_cents, int) or isinstance(amount_cents, bool) or amount_cents <= 0:
            raise ValueError("amount_cents must be an integer > 0")

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        sender = self.accounts[from_id]
        receiver = self.accounts[to_id]

        if sender["currency"] != receiver["currency"]:
            raise ValueError(
                f"Currency mismatch: {sender['currency']} vs {receiver['currency']}"
            )

        fee_cents = self._calculate_fee(amount_cents)
        total_debit = amount_cents + fee_cents

        if sender["balance"] < total_debit:
            raise ValueError(
                f"Insufficient funds: balance {sender['balance']} < required {total_debit}"
            )

        sender["balance"] -= total_debit
        sender["balance_cents"] = sender["balance"]

        if amount_cents >= HIGH_VALUE_THRESHOLD_CENTS:
            status = "AWAITING_CLEARING"
        else:
            status = "SETTLED"
            receiver["balance"] += amount_cents
            receiver["balance_cents"] = receiver["balance"]

        entry: Dict[str, Any] = {
            "tx_id": clean_tx_id,
            "from_acct": from_id,
            "to_acct": to_id,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "total_debit_cents": total_debit,
            "currency": sender["currency"],
            "timestamp": timestamp,
            "status": status,
        }
        self.transactions[clean_tx_id] = entry
        self.entries.append(entry)
        return dict(entry)

    def clear_transfer(self, tx_id: str) -> Dict[str, Any]:
        """Transitions an AWAITING_CLEARING transfer to SETTLED and credits amount_cents to to_acct."""
        if not isinstance(tx_id, str):
            raise KeyError(tx_id)
        clean_tx_id = tx_id.strip()
        if not clean_tx_id or clean_tx_id not in self.transactions:
            raise KeyError(tx_id)

        entry = self.transactions[clean_tx_id]
        if entry["status"] != "AWAITING_CLEARING":
            raise ValueError(
                f"Transfer {clean_tx_id} is in state {entry['status']!r}, expected 'AWAITING_CLEARING'"
            )

        receiver = self.accounts[entry["to_acct"]]
        receiver["balance"] += entry["amount_cents"]
        receiver["balance_cents"] = receiver["balance"]
        entry["status"] = "SETTLED"
        return dict(entry)

    def settle_pending(self, tx_id: str) -> Dict[str, Any]:
        """Backward-compatible alias that delegates to clear_transfer(tx_id)."""
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> Dict[str, Any]:
        """Reverses an AWAITING_CLEARING or SETTLED transfer, refunding principal + fee to sender."""
        if not isinstance(tx_id, str):
            raise KeyError(tx_id)
        clean_tx_id = tx_id.strip()
        if not clean_tx_id or clean_tx_id not in self.transactions:
            raise KeyError(tx_id)

        entry = self.transactions[clean_tx_id]
        status = entry["status"]
        if status == "REVERSED":
            raise ValueError(f"Transfer {clean_tx_id} is already 'REVERSED'")

        sender = self.accounts[entry["from_acct"]]
        receiver = self.accounts[entry["to_acct"]]
        amount_cents = entry["amount_cents"]
        fee_cents = entry["fee_cents"]

        if status == "AWAITING_CLEARING":
            sender["balance"] += amount_cents + fee_cents
            sender["balance_cents"] = sender["balance"]
            entry["status"] = "REVERSED"
            return dict(entry)

        if status == "SETTLED":
            if receiver["balance"] < amount_cents:
                raise ValueError("Recipient has insufficient funds to reverse")
            receiver["balance"] -= amount_cents
            receiver["balance_cents"] = receiver["balance"]
            sender["balance"] += amount_cents + fee_cents
            sender["balance_cents"] = sender["balance"]
            entry["status"] = "REVERSED"
            return dict(entry)

        raise ValueError(f"Cannot reverse transfer in state {status!r}")

    def total_collected_fees(self, currency: str = "USD") -> int:
        """Returns the sum of fee_cents across all non-reversed transfers in the specified currency."""
        if not isinstance(currency, str) or currency not in VALID_CURRENCIES:
            raise ValueError(f"Invalid currency: {currency!r}. Must be one of {sorted(VALID_CURRENCIES)}")

        return sum(
            int(entry["fee_cents"])
            for entry in self.entries
            if entry["currency"] == currency
            and entry["status"] in ("SETTLED", "AWAITING_CLEARING")
        )

    def account_statement(self, account_id: str) -> List[Dict[str, Any]]:
        """Returns copies of all transfers involving account_id sorted by (timestamp, insertion_index) ascending."""
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        clean_id = account_id.strip()
        if not clean_id or clean_id not in self.accounts:
            raise KeyError(account_id)

        matching = [
            (idx, entry)
            for idx, entry in enumerate(self.entries)
            if entry["from_acct"] == clean_id or entry["to_acct"] == clean_id
        ]
        matching.sort(key=lambda pair: (pair[1]["timestamp"], pair[0]))
        return [dict(entry) for _, entry in matching]
