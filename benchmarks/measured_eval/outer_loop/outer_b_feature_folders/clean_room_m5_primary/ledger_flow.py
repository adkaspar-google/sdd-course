from typing import Any, Dict, List


class LedgerFlow:
    """Multi-currency account and transfer settlement engine."""

    SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}
    PENDING_THRESHOLD_CENTS = 100_000

    def __init__(self) -> None:
        self.accounts: Dict[str, int] = {}
        self.account_records: Dict[str, Dict[str, Any]] = {}
        self.entries: List[Dict[str, Any]] = []
        self.transactions: Dict[str, Dict[str, Any]] = {}

    def open_account(
        self,
        account_id: str,
        currency: str = "USD",
        initial_cents: int = 0,
    ) -> dict:
        if not isinstance(account_id, str):
            raise ValueError("account_id must be a string")
        normalized_id = account_id.strip()
        if not normalized_id:
            raise ValueError("account_id must be non-empty")
        if normalized_id in self.accounts:
            raise ValueError(f"Duplicate account_id: {normalized_id}")

        if not isinstance(currency, str) or currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")

        if (
            not isinstance(initial_cents, int)
            or isinstance(initial_cents, bool)
            or initial_cents < 0
        ):
            raise ValueError("initial_cents must be a non-negative integer")

        self.accounts[normalized_id] = initial_cents
        record = {
            "account_id": normalized_id,
            "currency": currency,
            "balance": initial_cents,
            "balance_cents": initial_cents,
            "initial_cents": initial_cents,
        }
        self.account_records[normalized_id] = record
        return dict(record)

    def get_balance(self, account_id: str) -> int:
        if not isinstance(account_id, str):
            raise KeyError(account_id)
        normalized_id = account_id.strip()
        if normalized_id not in self.accounts:
            raise KeyError(normalized_id)
        return self.accounts[normalized_id]

    def post_transfer(
        self,
        tx_id: str,
        from_acct: str,
        to_acct: str,
        amount_cents: int,
        timestamp: int,
    ) -> dict:
        if not isinstance(tx_id, str):
            raise ValueError("tx_id must be a string")
        normalized_tx_id = tx_id.strip()
        if not normalized_tx_id:
            raise ValueError("tx_id must be non-empty")
        if normalized_tx_id in self.transactions:
            raise ValueError(f"Duplicate tx_id: {normalized_tx_id}")

        if not isinstance(from_acct, str):
            raise KeyError(from_acct)
        if not isinstance(to_acct, str):
            raise KeyError(to_acct)
        norm_from = from_acct.strip()
        norm_to = to_acct.strip()

        if norm_from not in self.accounts:
            raise KeyError(norm_from)
        if norm_to not in self.accounts:
            raise KeyError(norm_to)

        if norm_from == norm_to:
            raise ValueError("from_acct and to_acct must be distinct")

        if (
            not isinstance(amount_cents, int)
            or isinstance(amount_cents, bool)
            or amount_cents <= 0
        ):
            raise ValueError("amount_cents must be a positive integer")

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise ValueError("timestamp must be an integer")

        from_currency = self.account_records[norm_from]["currency"]
        to_currency = self.account_records[norm_to]["currency"]
        if from_currency != to_currency:
            raise ValueError("Currency mismatch between accounts")

        fee_cents = amount_cents // 100
        total_debit = amount_cents + fee_cents
        if self.accounts[norm_from] < total_debit:
            raise ValueError("Insufficient funds")

        self.accounts[norm_from] -= total_debit
        self.account_records[norm_from]["balance"] = self.accounts[norm_from]
        self.account_records[norm_from]["balance_cents"] = self.accounts[norm_from]

        if amount_cents > self.PENDING_THRESHOLD_CENTS:
            status = "PENDING"
        else:
            status = "SETTLED"
            self.accounts[norm_to] += amount_cents
            self.account_records[norm_to]["balance"] = self.accounts[norm_to]
            self.account_records[norm_to]["balance_cents"] = self.accounts[norm_to]

        entry = {
            "tx_id": normalized_tx_id,
            "from_acct": norm_from,
            "to_acct": norm_to,
            "amount_cents": amount_cents,
            "fee_cents": fee_cents,
            "currency": from_currency,
            "timestamp": timestamp,
            "status": status,
        }
        self.entries.append(entry)
        self.transactions[normalized_tx_id] = entry
        return dict(entry)
