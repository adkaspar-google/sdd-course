"""Clean-room implementation of LedgerFlow from EARS requirements and design specs."""

from typing import Any, Dict, List


class LedgerFlow:
    """In-memory transactional settlement ledger."""

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

    def _resolve_account_id(self, account_id: str) -> str:
        if not isinstance(account_id, str):
            raise KeyError("Account ID must be a string")
        cleaned = account_id.strip()
        if cleaned not in self._accounts:
            raise KeyError(f"Unknown account: {account_id}")
        return cleaned

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> Dict[str, Any]:
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        cleaned_id = account_id.strip()
        if not cleaned_id:
            raise ValueError("account_id must be non-empty")
        if cleaned_id in self._accounts:
            raise ValueError(f"Duplicate account_id: {cleaned_id}")

        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        cleaned_currency = currency.strip().upper()
        if cleaned_currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

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
        resolved_id = self._resolve_account_id(account_id)
        return self._accounts[resolved_id]["balance"]

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int = 0,
    ) -> Dict[str, Any]:
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ValueError("tx_id must be a non-empty string")
        cleaned_tx_id = tx_id.strip()

        if cleaned_tx_id in self._tx_index:
            existing = self._tx_index[cleaned_tx_id]
            norm_from = from_acct.strip() if isinstance(from_acct, str) else from_acct
            norm_to = to_acct.strip() if isinstance(to_acct, str) else to_acct
            if (
                not isinstance(amount_cents, bool)
                and existing["from_acct"] == norm_from
                and existing["to_acct"] == norm_to
                and existing["amount_cents"] == amount_cents
            ):
                return dict(existing)
            raise ValueError("Conflicting tx_id")

        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        sender_id = self._resolve_account_id(from_acct)
        receiver_id = self._resolve_account_id(to_acct)

        if sender_id == receiver_id:
            raise ValueError("from_acct and to_acct must be different")

        sender = self._accounts[sender_id]
        receiver = self._accounts[receiver_id]

        if sender["currency"] != receiver["currency"]:
            raise ValueError("Currency mismatch between accounts")

        if amount_cents >= self.CLEARING_THRESHOLD_CENTS:
            fee_cents = max(10, (amount_cents * 50) // 10000)
            status = "AWAITING_CLEARING"
        else:
            fee_cents = max(10, amount_cents // 100)
            status = "SETTLED"

        total_debit = amount_cents + fee_cents
        if sender["balance"] < total_debit:
            raise ValueError("Insufficient funds")

        self._set_balance(sender_id, sender["balance"] - total_debit)
        if status == "SETTLED":
            self._set_balance(receiver_id, receiver["balance"] + amount_cents)

        entry: Dict[str, Any] = {
            "tx_id": cleaned_tx_id,
            "from_acct": sender_id,
            "to_acct": receiver_id,
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
        if not isinstance(tx_id, str):
            raise KeyError("tx_id must be a string")
        cleaned_tx_id = tx_id.strip()
        if cleaned_tx_id not in self._tx_index:
            raise KeyError(f"Unknown tx_id: {tx_id}")

        entry = self._tx_index[cleaned_tx_id]
        if entry["status"] != "AWAITING_CLEARING":
            raise ValueError(
                f"Transfer {cleaned_tx_id} is not in AWAITING_CLEARING status"
            )

        receiver_id = entry["to_acct"]
        receiver = self._accounts[receiver_id]
        self._set_balance(receiver_id, receiver["balance"] + entry["amount_cents"])
        entry["status"] = "SETTLED"
        return dict(entry)

    def settle_pending(self, tx_id: str) -> Dict[str, Any]:
        return self.clear_transfer(tx_id)

    def reverse_transfer(self, tx_id: str) -> Dict[str, Any]:
        if not isinstance(tx_id, str):
            raise KeyError("tx_id must be a string")
        cleaned_tx_id = tx_id.strip()
        if cleaned_tx_id not in self._tx_index:
            raise KeyError(f"Unknown tx_id: {tx_id}")

        entry = self._tx_index[cleaned_tx_id]
        status = entry["status"]
        if status == "REVERSED":
            raise ValueError(f"Transfer {cleaned_tx_id} is already reversed")

        sender_id = entry["from_acct"]
        receiver_id = entry["to_acct"]
        amount_cents = entry["amount_cents"]
        fee_cents = entry["fee_cents"]

        if status == "AWAITING_CLEARING":
            sender = self._accounts[sender_id]
            self._set_balance(sender_id, sender["balance"] + amount_cents + fee_cents)
            entry["status"] = "REVERSED"
            return dict(entry)

        if status == "SETTLED":
            receiver = self._accounts[receiver_id]
            if receiver["balance"] < amount_cents:
                raise ValueError("Recipient has insufficient funds to reverse")
            sender = self._accounts[sender_id]
            self._set_balance(receiver_id, receiver["balance"] - amount_cents)
            self._set_balance(sender_id, sender["balance"] + amount_cents + fee_cents)
            entry["status"] = "REVERSED"
            return dict(entry)

        raise ValueError(f"Unsupported transfer status for reversal: {status}")

    def total_collected_fees(self, currency: str = "USD") -> int:
        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        cleaned_currency = currency.strip().upper()
        if cleaned_currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        return sum(
            entry["fee_cents"]
            for entry in self.entries
            if entry["currency"] == cleaned_currency
            and entry["status"] in ("SETTLED", "AWAITING_CLEARING")
        )

    def account_statement(self, account_id: str) -> List[Dict[str, Any]]:
        resolved_id = self._resolve_account_id(account_id)
        matches = [
            (idx, entry)
            for idx, entry in enumerate(self.entries)
            if entry["from_acct"] == resolved_id or entry["to_acct"] == resolved_id
        ]
        matches.sort(key=lambda pair: (pair[1]["timestamp"], pair[0]))
        return [dict(entry) for _, entry in matches]
