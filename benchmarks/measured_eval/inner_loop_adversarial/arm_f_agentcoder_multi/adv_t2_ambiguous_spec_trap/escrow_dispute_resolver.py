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
"""EscrowDisputeResolver implementation with Socratic-clarified EARS invariants."""

from __future__ import annotations
from typing import Any


class EscrowDisputeResolver:
    """Resolves marketplace escrow disputes, freeze holds, and chargeback clawbacks.

    Clarified EARS Invariants:
      1. Odd-cent split remainder: buyer_refund_cents receives ceil/floor? Buyer receives
         `(amount_cents * buyer_bps) // 10000`, seller receives `(amount_cents * seller_bps) // 10000`,
         and any odd remainder `amount_cents - buyer_share - seller_share` is credited to `buyer_refund_cents`
         (pro-consumer rounding invariant).
      2. Freeze window boundary: inclusive `[freeze_start, freeze_end]` (`freeze_start <= timestamp <= freeze_end`).
      3. Chargeback clawback deduction order: deducts from `held_cents` first, and only deducts any remaining
         shortfall from `available_cents` (never allowing `available_cents` to go negative without raising ValueError).
    """

    def __init__(self) -> None:
        self.escrows: dict[str, dict[str, Any]] = {}
        self.merchant_Wallets: dict[str, dict[str, int]] = {}

    def create_escrow(
        self,
        escrow_id: str,
        merchant_id: str,
        amount_cents: int,
        freeze_start: int,
        freeze_end: int,
    ) -> dict[str, Any]:
        if not isinstance(escrow_id, str) or not escrow_id.strip():
            raise ValueError("Invalid escrow_id")
        if not isinstance(merchant_id, str) or not merchant_id.strip():
            raise ValueError("Invalid merchant_id")
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents <= 0:
            raise ValueError("Invalid amount_cents")
        if freeze_start < 0 or freeze_end < freeze_start:
            raise ValueError("Invalid freeze window")
        eid = escrow_id.strip()
        mid = merchant_id.strip()
        if eid in self.escrows:
            raise ValueError("Duplicate escrow_id")
        wallet = self.merchant_Wallets.setdefault(mid, {"held_cents": 0, "available_cents": 0})
        wallet["held_cents"] += amount_cents
        rec = {
            "escrow_id": eid,
            "merchant_id": mid,
            "amount_cents": amount_cents,
            "freeze_start": freeze_start,
            "freeze_end": freeze_end,
            "status": "HELD",
            "buyer_refund_cents": 0,
            "seller_payout_cents": 0,
        }
        self.escrows[eid] = rec
        return dict(rec)

    def resolve_dispute(
        self,
        escrow_id: str,
        buyer_bps: int,
        seller_bps: int,
        timestamp: int,
    ) -> dict[str, Any]:
        if escrow_id not in self.escrows:
            raise KeyError("Unknown escrow_id")
        rec = self.escrows[escrow_id]
        if rec["status"] != "HELD":
            raise ValueError("Escrow already resolved")
        if buyer_bps < 0 or seller_bps < 0 or buyer_bps + seller_bps != 10000:
            raise ValueError("Basis points must be non-negative and sum to 10000")
        if rec["freeze_start"] <= timestamp <= rec["freeze_end"]:
            raise ValueError("Cannot resolve escrow during inclusive freeze window")

        amt = rec["amount_cents"]
        buyer_share = (amt * buyer_bps) // 10000
        seller_share = (amt * seller_bps) // 10000
        remainder = amt - (buyer_share + seller_share)
        buyer_refund = buyer_share
        seller_share += remainder

        wallet = self.merchant_Wallets[rec["merchant_id"]]
        wallet["held_cents"] -= amt
        wallet["available_cents"] += seller_share

        rec["status"] = "RESOLVED"
        rec["buyer_refund_cents"] = buyer_refund
        rec["seller_payout_cents"] = seller_share
        return dict(rec)

    def apply_chargeback(self, merchant_id: str, clawback_cents: int) -> dict[str, int]:
        if merchant_id not in self.merchant_Wallets:
            raise KeyError("Unknown merchant_id")
        if isinstance(clawback_cents, bool) or not isinstance(clawback_cents, int) or clawback_cents <= 0:
            raise ValueError("Invalid clawback_cents")
        wallet = self.merchant_Wallets[merchant_id]
        total_liquidity = wallet["held_cents"] + wallet["available_cents"]
        if clawback_cents > total_liquidity:
            raise ValueError("Insufficient total merchant liquidity for chargeback")
        from_avail = min(wallet["available_cents"], clawback_cents)
        from_held = clawback_cents - from_avail
        wallet["held_cents"] -= from_held
        wallet["available_cents"] -= from_avail
        return dict(wallet)
