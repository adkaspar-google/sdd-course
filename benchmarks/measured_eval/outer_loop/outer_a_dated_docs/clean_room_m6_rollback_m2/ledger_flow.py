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
"""Milestone 2 Clean-Room Reconstructed LedgerFlow (M1 Core + M2 Idempotency & Statement)."""

from __future__ import annotations
from typing import Any

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}


class LedgerFlow:
    def __init__(self) -> None:
        self.accounts: dict[str, dict[str, Any]] = {}
        self.transactions: dict[str, dict[str, Any]] = {}

    def open_account(self, account_id: str, currency: str, initial_balance_cents: int = 0) -> dict[str, Any]:
        if not isinstance(account_id, str) or not account_id.strip():
            raise ValueError("Invalid account_id")
        aid = account_id.strip()
        if aid in self.accounts:
            raise ValueError("Duplicate account_id")
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Unsupported currency")
        if isinstance(initial_balance_cents, bool) or not isinstance(initial_balance_cents, int) or initial_balance_cents < 0:
            raise ValueError("Invalid initial_balance_cents")
        rec = {"account_id": aid, "currency": currency, "balance_cents": initial_balance_cents}
        self.accounts[aid] = rec
        return dict(rec)

    def get_balance(self, account_id: str) -> int:
        if not isinstance(account_id, str) or account_id.strip() not in self.accounts:
            raise KeyError("Unknown account_id")
        return self.accounts[account_id.strip()]["balance_cents"]

    def post_transfer(
        self,
        tx_id: str,
        sender_id: str,
        recipient_id: str,
        amount_cents: int,
        timestamp: int,
    ) -> dict[str, Any]:
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("Invalid tx_id")
        tid = tx_id.strip()
        if tid in self.transactions:
            existing = self.transactions[tid]
            if (
                existing["sender_id"] == sender_id
                and existing["recipient_id"] == recipient_id
                and existing["amount_cents"] == amount_cents
            ):
                return dict(existing)
            raise ValueError("Idempotency conflict on tx_id")

        if sender_id not in self.accounts or recipient_id not in self.accounts:
            raise KeyError("Unknown account")
        if sender_id == recipient_id or amount_cents <= 0:
            raise ValueError("Invalid transfer parameters")
        s_acc = self.accounts[sender_id]
        r_acc = self.accounts[recipient_id]
        if s_acc["currency"] != r_acc["currency"]:
            raise ValueError("Currency mismatch")

        # Milestone 1-2 invariant: flat 1% integer division fee (no 10-cent floor, no 50 bps tier)
        fee_cents = amount_cents // 100
        total_debit = amount_cents + fee_cents
        if s_acc["balance_cents"] < total_debit:
            raise ValueError("Insufficient funds")

        s_acc["balance_cents"] -= total_debit
        # Milestone 1-2 invariant: strict > 100000 threshold and 'PENDING' status
        if amount_cents > 100000:
            status = "PENDING"
        else:
            status = "SETTLED"
            r_acc["balance_cents"] += amount_cents

        tx = {
            "tx_id": tid,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "currency": s_acc["currency"],
            "timestamp": timestamp,
            "status": status,
        }
        self.transactions[tid] = tx
        return dict(tx)

    def settle_pending(self, tx_id: str) -> dict[str, Any]:
        if tx_id not in self.transactions:
            raise KeyError("Unknown tx_id")
        tx = self.transactions[tx_id]
        if tx["status"] != "PENDING":
            raise ValueError("Transfer is not PENDING")
        self.accounts[tx["recipient_id"]]["balance_cents"] += tx["amount_cents"]
        tx["status"] = "SETTLED"
        return dict(tx)

    def account_statement(self, account_id: str) -> list[dict[str, Any]]:
        if account_id not in self.accounts:
            raise KeyError("Unknown account_id")
        txs = [
            dict(tx)
            for tx in self.transactions.values()
            if tx["sender_id"] == account_id or tx["recipient_id"] == account_id
        ]
        txs.sort(key=lambda t: (t["timestamp"], t["tx_id"]))
        return txs
