"""Outer-Loop M1->M5 Continuous Evolution: LedgerFlow."""

from typing import Any, Dict, List


class LedgerFlow:
    """Multi-milestone settlement ledger."""

    SUPPORTED_CURRENCIES = ("USD", "EUR", "GBP")
    CLEARING_THRESHOLD_CENTS = 100_000

    def __init__(self) -> None:
        self.accounts: Dict[str, int] = {}
        self.account_records: Dict[str, Dict[str, Any]] = {}
        self.entries: List[Dict[str, Any]] = []
        self.transactions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _calculate_fee(cls, amount_cents: int) -> int:
        """Computes tiered platform fee with a 10-cent minimum floor."""
        if amount_cents >= cls.CLEARING_THRESHOLD_CENTS:
            return max(10, (amount_cents * 50) // 10000)
        return max(10, amount_cents // 100)

    def _set_account_balance(self, acct_id: str, new_balance: int) -> None:
        self.accounts[acct_id] = new_balance
        self.account_records[acct_id]["balance"] = new_balance
        self.account_records[acct_id]["balance_cents"] = new_balance

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> Dict[str, Any]:
        """Creates a new account with trimmed ID, valid 3-letter currency, and non-negative balance."""
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        acct_id = account_id.strip()
        if not acct_id:
            raise ValueError("account_id must be non-empty")
        if acct_id in self.accounts:
            raise ValueError(f"Duplicate account_id: {acct_id}")

        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be a non-negative integer")

        self.accounts[acct_id] = initial_cents
        record = {
            "account_id": acct_id,
            "currency": currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
        }
        self.account_records[acct_id] = record
        return dict(record)

    def get_balance(self, account_id: str) -> int:
        """Returns current integer balance in cents for account_id."""
        acct_id = account_id.strip() if isinstance(account_id, str) else account_id
        if acct_id not in self.accounts:
            raise KeyError(f"Unknown account_id: {account_id}")
        return self.accounts[acct_id]

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> Dict[str, Any]:
        """Posts a same-currency transfer with replay-safe idempotency and tiered fees."""
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string")
        clean_tx_id = tx_id.strip()

        src = from_acct.strip() if isinstance(from_acct, str) else from_acct
        dst = to_acct.strip() if isinstance(to_acct, str) else to_acct

        if clean_tx_id in self.transactions:
            existing = self.transactions[clean_tx_id]
            if (
                existing["from_acct"] == src
                and existing["to_acct"] == dst
                and existing["amount_cents"] == amount_cents
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        if src not in self.accounts:
            raise KeyError(f"Unknown source account: {from_acct}")
        if dst not in self.accounts:
            raise KeyError(f"Unknown destination account: {to_acct}")

        if src == dst:
            raise ValueError("from_acct and to_acct must be distinct")

        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        src_curr = self.account_records[src]["currency"]
        dst_curr = self.account_records[dst]["currency"]
        if src_curr != dst_curr:
            raise ValueError(f"Currency mismatch: {src_curr} vs {dst_curr}")

        fee_cents = self._calculate_fee(amount_cents)
        total_debit = amount_cents + fee_cents
        if self.accounts[src] < total_debit:
            raise ValueError("Insufficient funds")

        self._set_account_balance(src, self.accounts[src] - total_debit)

        if amount_cents >= self.CLEARING_THRESHOLD_CENTS:
            status = "AWAITING_CLEARING"
        else:
            status = "SETTLED"
            self._set_account_balance(dst, self.accounts[dst] + amount_cents)

        entry: Dict[str, Any] = {
            "tx_id": clean_tx_id,
            "from_acct": src,
            "to_acct": dst,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "currency": src_curr,
            "timestamp": timestamp,
            "status": status,
        }
        self.entries.append(entry)
        self.transactions[clean_tx_id] = entry
        return dict(entry)

    def clear_transfer(self, tx_id: str) -> Dict[str, Any]:
        """Transitions an AWAITING_CLEARING transfer to SETTLED and credits amount_cents to to_acct."""
        clean_tx_id = tx_id.strip() if isinstance(tx_id, str) else tx_id
        if clean_tx_id not in self.transactions:
            raise KeyError(f"Unknown tx_id: {tx_id}")

        entry = self.transactions[clean_tx_id]
        if entry["status"] != "AWAITING_CLEARING":
            raise ValueError(f"Transfer {clean_tx_id} is not in AWAITING_CLEARING state")

        entry["status"] = "SETTLED"
        dst = entry["to_acct"]
        self._set_account_balance(dst, self.accounts[dst] + entry["amount_cents"])
        return dict(entry)

    def settle_pending(self, tx_id: str) -> Dict[str, Any]:
        """Backward-compatible alias that delegates to clear_transfer(tx_id)."""
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> Dict[str, Any]:
        """Reverses an AWAITING_CLEARING or SETTLED transfer and refunds sender including fee."""
        clean_tx_id = tx_id.strip() if isinstance(tx_id, str) else tx_id
        if clean_tx_id not in self.transactions:
            raise KeyError(f"Unknown tx_id: {tx_id}")

        entry = self.transactions[clean_tx_id]
        status = entry["status"]
        if status == "REVERSED":
            raise ValueError(f"Transfer {clean_tx_id} is already REVERSED")

        src = entry["from_acct"]
        dst = entry["to_acct"]
        amount_cents = entry["amount_cents"]
        fee_cents = entry["fee_cents"]

        if status == "AWAITING_CLEARING":
            self._set_account_balance(src, self.accounts[src] + amount_cents + fee_cents)
            entry["status"] = "REVERSED"
            return dict(entry)

        if status == "SETTLED":
            if self.accounts[dst] < amount_cents:
                raise ValueError("Recipient has insufficient funds to reverse")
            self._set_account_balance(dst, self.accounts[dst] - amount_cents)
            self._set_account_balance(src, self.accounts[src] + amount_cents + fee_cents)
            entry["status"] = "REVERSED"
            return dict(entry)

        raise ValueError(f"Cannot reverse transfer in status {status}")

    def total_collected_fees(self, currency: str = "USD") -> int:
        """Returns the sum of fee_cents across all non-reversed transfers in the given currency."""
        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        return sum(
            entry["fee_cents"]
            for entry in self.entries
            if entry["currency"] == currency
            and entry["status"] in ("SETTLED", "AWAITING_CLEARING")
        )

    def account_statement(self, account_id: str) -> List[Dict[str, Any]]:
        """Returns copies of all transfers involving account_id sorted by (timestamp, insertion_index) ascending."""
        acct_id = account_id.strip() if isinstance(account_id, str) else account_id
        if acct_id not in self.accounts:
            raise KeyError(f"Unknown account_id: {account_id}")

        matching = [
            (idx, entry)
            for idx, entry in enumerate(self.entries)
            if entry["from_acct"] == acct_id or entry["to_acct"] == acct_id
        ]
        matching.sort(key=lambda item: (item[1]["timestamp"], item[0]))
        return [dict(entry) for _, entry in matching]
