"""Clean-room implementation of LedgerFlow from surviving specification folders."""

from typing import Any, Dict, List


class LedgerFlow:
    """Multi-currency account and transfer settlement engine."""

    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}
    PENDING_THRESHOLD_CENTS = 100_000
    CLEARING_THRESHOLD_CENTS = 100_000

    def __init__(self) -> None:
        self.accounts: Dict[str, int] = {}
        self.account_records: Dict[str, Dict[str, Any]] = {}
        self.entries: List[Dict[str, Any]] = []
        self.transactions: Dict[str, Dict[str, Any]] = {}

    def _update_balance(self, account_id: str, new_balance_cents: int) -> None:
        self.accounts[account_id] = new_balance_cents
        self.account_records[account_id]["balance"] = new_balance_cents
        self.account_records[account_id]["balance_cents"] = new_balance_cents

    @staticmethod
    def _calculate_fee(amount_cents: int) -> int:
        if amount_cents >= 100_000:
            return max(10, (amount_cents * 50) // 10000)
        return max(10, amount_cents // 100)

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> Dict[str, Any]:
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        clean_id = account_id.strip()
        if not clean_id:
            raise ValueError("account_id must be non-empty")
        if clean_id in self.accounts:
            raise ValueError(f"Duplicate account_id: {clean_id}")
        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be a non-negative integer")

        self.accounts[clean_id] = initial_cents
        record: Dict[str, Any] = {
            "account_id": clean_id,
            "currency": currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
            "initial_cents": initial_cents,
        }
        self.account_records[clean_id] = record
        return dict(record)

    def get_balance(self, account_id: str) -> int:
        if not isinstance(account_id, str):
            raise KeyError(f"Unknown account_id: {account_id}")
        clean_id = account_id.strip()
        if clean_id not in self.accounts:
            raise KeyError(f"Unknown account_id: {clean_id}")
        return self.accounts[clean_id]

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
        clean_tx_id = tx_id.strip()
        src = from_acct.strip() if isinstance(from_acct, str) else from_acct
        dst = to_acct.strip() if isinstance(to_acct, str) else to_acct

        if clean_tx_id in self.transactions:
            existing = self.transactions[clean_tx_id]
            if (
                not isinstance(amount_cents, bool)
                and (
                    existing["from_acct"],
                    existing["to_acct"],
                    existing["amount_cents"],
                )
                == (src, dst, amount_cents)
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        if not isinstance(src, str) or src not in self.accounts:
            raise KeyError(f"Unknown source account: {from_acct}")
        if not isinstance(dst, str) or dst not in self.accounts:
            raise KeyError(f"Unknown destination account: {to_acct}")
        if src == dst:
            raise ValueError("Source and destination accounts must be distinct")
        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")
        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        src_currency = self.account_records[src]["currency"]
        dst_currency = self.account_records[dst]["currency"]
        if src_currency != dst_currency:
            raise ValueError("Currency mismatch between accounts")

        fee_cents = self._calculate_fee(amount_cents)
        total_debit = amount_cents + fee_cents
        if self.accounts[src] < total_debit:
            raise ValueError("Insufficient funds")

        self._update_balance(src, self.accounts[src] - total_debit)

        if amount_cents >= self.CLEARING_THRESHOLD_CENTS:
            status = "AWAITING_CLEARING"
        else:
            status = "SETTLED"
            self._update_balance(dst, self.accounts[dst] + amount_cents)

        entry: Dict[str, Any] = {
            "tx_id": clean_tx_id,
            "from_acct": src,
            "to_acct": dst,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "currency": src_currency,
            "timestamp": timestamp,
            "status": status,
        }
        self.entries.append(entry)
        self.transactions[clean_tx_id] = entry
        return dict(entry)

    def clear_transfer(self, tx_id: str) -> Dict[str, Any]:
        clean_tx_id = tx_id.strip() if isinstance(tx_id, str) else tx_id
        if not isinstance(clean_tx_id, str) or clean_tx_id not in self.transactions:
            raise KeyError(f"Unknown tx_id: {tx_id}")
        entry = self.transactions[clean_tx_id]
        if entry["status"] != "AWAITING_CLEARING":
            raise ValueError(
                f"Transfer {clean_tx_id} is not in AWAITING_CLEARING status"
            )
        entry["status"] = "SETTLED"
        dst = entry["to_acct"]
        self._update_balance(dst, self.accounts[dst] + entry["amount_cents"])
        return dict(entry)

    def settle_pending(self, tx_id: str) -> Dict[str, Any]:
        return self.clear_transfer(tx_id)

    def account_statement(self, account_id: str) -> List[Dict[str, Any]]:
        acct_id = account_id.strip() if isinstance(account_id, str) else account_id
        if not isinstance(acct_id, str) or acct_id not in self.accounts:
            raise KeyError(f"Unknown account_id: {account_id}")
        matches = [
            (idx, entry)
            for idx, entry in enumerate(self.entries)
            if entry["from_acct"] == acct_id or entry["to_acct"] == acct_id
        ]
        matches.sort(key=lambda item: (item[1]["timestamp"], item[0]))
        return [dict(entry) for _, entry in matches]

    def reverse_transfer(self, tx_id: str) -> Dict[str, Any]:
        clean_tx_id = tx_id.strip() if isinstance(tx_id, str) else tx_id
        if not isinstance(clean_tx_id, str) or clean_tx_id not in self.transactions:
            raise KeyError(f"Unknown tx_id: {tx_id}")
        entry = self.transactions[clean_tx_id]
        if entry["status"] == "REVERSED":
            raise ValueError(f"Transfer {clean_tx_id} is already REVERSED")

        src = entry["from_acct"]
        dst = entry["to_acct"]
        amount = entry["amount_cents"]
        fee = entry["fee_cents"]

        if entry["status"] == "AWAITING_CLEARING":
            self._update_balance(src, self.accounts[src] + amount + fee)
            entry["status"] = "REVERSED"
        elif entry["status"] == "SETTLED":
            if self.accounts[dst] < amount:
                raise ValueError("Recipient has insufficient funds to reverse")
            self._update_balance(dst, self.accounts[dst] - amount)
            self._update_balance(src, self.accounts[src] + amount + fee)
            entry["status"] = "REVERSED"
        else:
            raise ValueError(f"Cannot reverse transfer in status {entry['status']}")

        return dict(entry)

    def total_collected_fees(self, currency: str = "USD") -> int:
        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        return sum(
            entry["fee_cents"]
            for entry in self.entries
            if entry["currency"] == currency
            and entry["status"] in ("SETTLED", "AWAITING_CLEARING")
        )
