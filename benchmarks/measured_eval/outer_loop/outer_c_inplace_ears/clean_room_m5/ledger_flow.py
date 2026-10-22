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
"""LedgerFlow — Clean-room implementation from EARS requirements and technical design."""

from typing import Any, Dict, List


class LedgerFlow:
    """In-memory multi-currency settlement ledger with tiered fees, clearing, idempotency, and reversals."""

    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}
    CLEARING_THRESHOLD_CENTS = 100000

    def __init__(self) -> None:
        self._accounts: Dict[str, Dict[str, Any]] = {}
        self.accounts: Dict[str, int] = {}
        self.entries: List[Dict[str, Any]] = []
        self._tx_index: Dict[str, Dict[str, Any]] = {}

    def _set_balance(self, account_id: str, new_balance: int) -> None:
        acct = self._accounts[account_id]
        acct["balance"] = new_balance
        acct["balance_cents"] = new_balance
        self.accounts[account_id] = new_balance

    def open_account(
        self, account_id: str, currency: str = "USD", initial_cents: int = 0
    ) -> Dict[str, Any]:
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        cleaned_id = account_id.strip()
        if not cleaned_id or cleaned_id in self._accounts:
            raise ValueError(f"Invalid or duplicate account_id: {account_id!r}")

        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        cleaned_currency = currency.strip().upper()
        if cleaned_currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency!r}")

        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be a non-negative integer")

        acct: Dict[str, Any] = {
            "account_id": cleaned_id,
            "currency": cleaned_currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
        }
        self._accounts[cleaned_id] = acct
        self.accounts[cleaned_id] = initial_cents
        return dict(acct)

    def get_balance(self, account_id: str) -> int:
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        cleaned_id = account_id.strip()
        if cleaned_id not in self._accounts:
            raise KeyError(account_id)
        return self._accounts[cleaned_id]["balance"]

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> Dict[str, Any]:
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string")
        cleaned_tx_id = tx_id.strip()

        from_id = from_acct.strip() if isinstance(from_acct, str) else from_acct
        to_id = to_acct.strip() if isinstance(to_acct, str) else to_acct

        # REQ-M3-001 & REQ-M3-002: Replay-safe idempotency gate
        if cleaned_tx_id in self._tx_index:
            existing = self._tx_index[cleaned_tx_id]
            if (
                not isinstance(amount_cents, bool)
                and existing["from_acct"] == from_id
                and existing["to_acct"] == to_id
                and existing["amount_cents"] == amount_cents
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        # REQ-M1-005: Account existence validation
        if not isinstance(from_id, str) or from_id not in self._accounts:
            raise KeyError(from_acct)
        if not isinstance(to_id, str) or to_id not in self._accounts:
            raise KeyError(to_acct)

        # REQ-M1-006: Parameter and constitutional no-overdraft validation
        if from_id == to_id:
            raise ValueError("Self-transfers are not permitted")
        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")
        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        sender = self._accounts[from_id]
        recipient = self._accounts[to_id]
        if sender["currency"] != recipient["currency"]:
            raise ValueError("Currency mismatch between accounts")

        # REQ-M1-007 & REQ-M1-008: Tiered fee calculation & clearing threshold
        if amount_cents >= self.CLEARING_THRESHOLD_CENTS:
            fee_cents = max(10, (amount_cents * 50) // 10000)
            status = "AWAITING_CLEARING"
        else:
            fee_cents = max(10, amount_cents // 100)
            status = "SETTLED"

        total_debit = amount_cents + fee_cents
        if sender["balance"] < total_debit:
            raise ValueError("Insufficient funds: overdraft prohibited")

        self._set_balance(from_id, sender["balance"] - total_debit)
        if status == "SETTLED":
            self._set_balance(to_id, recipient["balance"] + amount_cents)

        entry: Dict[str, Any] = {
            "tx_id": cleaned_tx_id,
            "from_acct": from_id,
            "to_acct": to_id,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "currency": sender["currency"],
            "timestamp": timestamp,
            "status": status,
        }
        self.entries.append(entry)
        self._tx_index[cleaned_tx_id] = entry
        return dict(entry)

    def clear_transfer(self, tx_id: str) -> Dict[str, Any]:
        if not isinstance(tx_id, str) or tx_id.strip() not in self._tx_index:
            raise KeyError(tx_id)
        entry = self._tx_index[tx_id.strip()]
        if entry["status"] != "AWAITING_CLEARING":
            raise ValueError(
                f"Transfer {tx_id!r} cannot be cleared from status {entry['status']!r}"
            )
        to_id = entry["to_acct"]
        self._set_balance(to_id, self._accounts[to_id]["balance"] + entry["amount_cents"])
        entry["status"] = "SETTLED"
        return dict(entry)

    def settle_pending(self, tx_id: str) -> Dict[str, Any]:
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> Dict[str, Any]:
        if not isinstance(tx_id, str) or tx_id.strip() not in self._tx_index:
            raise KeyError(tx_id)
        entry = self._tx_index[tx_id.strip()]
        status = entry["status"]
        if status == "REVERSED":
            raise ValueError(f"Transfer {tx_id!r} is already REVERSED")

        from_id = entry["from_acct"]
        to_id = entry["to_acct"]
        amount_cents = entry["amount_cents"]
        fee_cents = entry["fee_cents"]

        if status == "AWAITING_CLEARING":
            self._set_balance(
                from_id, self._accounts[from_id]["balance"] + amount_cents + fee_cents
            )
            entry["status"] = "REVERSED"
            return dict(entry)

        if status == "SETTLED":
            if self._accounts[to_id]["balance"] < amount_cents:
                raise ValueError("Recipient has insufficient funds to reverse")
            self._set_balance(to_id, self._accounts[to_id]["balance"] - amount_cents)
            self._set_balance(
                from_id, self._accounts[from_id]["balance"] + amount_cents + fee_cents
            )
            entry["status"] = "REVERSED"
            return dict(entry)

        raise ValueError(f"Unsupported transfer status for reversal: {status!r}")

    def total_collected_fees(self, currency: str = "USD") -> int:
        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        cleaned_currency = currency.strip().upper()
        if cleaned_currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency!r}")
        return sum(
            e["fee_cents"]
            for e in self.entries
            if e["currency"] == cleaned_currency
            and e["status"] in ("SETTLED", "AWAITING_CLEARING")
        )

    def account_statement(self, account_id: str) -> List[Dict[str, Any]]:
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        resolved_id = account_id.strip()
        if resolved_id not in self._accounts:
            raise KeyError(account_id)
        matches = [
            (idx, entry)
            for idx, entry in enumerate(self.entries)
            if entry["from_acct"] == resolved_id or entry["to_acct"] == resolved_id
        ]
        matches.sort(key=lambda pair: (pair[1]["timestamp"], pair[0]))
        return [dict(entry) for _, entry in matches]
