from enum import StrEnum


class AccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

    @property
    def debit_normal(self) -> bool:
        """Assets and expenses grow with debits; everything else with credits."""
        return self in (AccountType.ASSET, AccountType.EXPENSE)

    @property
    def is_temporary(self) -> bool:
        """Revenue and expense accounts start from zero every fiscal year."""
        return self in (AccountType.REVENUE, AccountType.EXPENSE)
