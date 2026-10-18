from __future__ import annotations

import uuid
from collections.abc import Mapping

from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.revenue_recognition import RevenueRecognition
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine

Roles = Mapping[AccountRole, uuid.UUID]


class SalesPostingPolicy:
    """How a paid ticket, its earning and its refund look in the books.

    Customers always pay the ticket price as shown, so VAT (when the business is VAT-registered) is carved out of that
    price, never added on top.
    """

    @staticmethod
    def vat_part(gross_irr: int, vat_percent: int) -> int:
        return gross_irr * vat_percent // (100 + vat_percent) if vat_percent else 0

    @classmethod
    def sale_lines(
        cls,
        *,
        gross_irr: int,
        receipt_account_id: uuid.UUID,
        roles: Roles,
        settings: AccountingSettings,
        online: bool,
        memo: str,
    ) -> list[JournalLine]:
        vat = cls.vat_part(gross_irr, settings.vat_percent)
        net = gross_irr - vat
        earned_role = (
            AccountRole.DEFERRED_REVENUE
            if settings.revenue_recognition is RevenueRecognition.ON_SESSION
            else AccountRole.SALES_REVENUE
        )
        lines = [
            JournalLine(receipt_account_id, debit_irr=gross_irr, memo=memo),
            JournalLine(roles[earned_role], credit_irr=net, memo=memo),
        ]
        if vat:
            lines.append(JournalLine(roles[AccountRole.VAT_PAYABLE], credit_irr=vat, memo=memo))
        fee = gross_irr * settings.gateway_fee_bp // 10_000 if online else 0
        if fee:
            lines.append(JournalLine(roles[AccountRole.GATEWAY_FEES], debit_irr=fee, memo="کارمزد درگاه"))
            lines.append(JournalLine(receipt_account_id, credit_irr=fee, memo="کارمزد درگاه"))
        return lines

    @staticmethod
    def deferred_amount(sale: JournalEntry, roles: Roles) -> int:
        """How much of a sale was parked as a customer advance (zero when it was booked as revenue straight away)."""
        deferred = roles[AccountRole.DEFERRED_REVENUE]
        return sum(line.credit_irr for line in sale.lines if line.account_id == deferred)

    @classmethod
    def recognition_lines(cls, sale: JournalEntry, roles: Roles, memo: str) -> list[JournalLine]:
        net = cls.deferred_amount(sale, roles)
        return [
            JournalLine(roles[AccountRole.DEFERRED_REVENUE], debit_irr=net, memo=memo),
            JournalLine(roles[AccountRole.SALES_REVENUE], credit_irr=net, memo=memo),
        ]

    @classmethod
    def refund_lines(
        cls,
        sale: JournalEntry,
        *,
        roles: Roles,
        recognized: bool,
        credit_account_id: uuid.UUID,
        memo: str,
    ) -> list[JournalLine]:
        """Gives the sale back to the customer: revenue (or advance) and VAT are undone, the payment fee is kept."""
        vat_account = roles[AccountRole.VAT_PAYABLE]
        net_accounts = {roles[AccountRole.SALES_REVENUE], roles[AccountRole.DEFERRED_REVENUE]}
        net = sum(line.credit_irr for line in sale.lines if line.account_id in net_accounts)
        vat = sum(line.credit_irr for line in sale.lines if line.account_id == vat_account)
        deferred_unearned = cls.deferred_amount(sale, roles) > 0 and not recognized
        net_account = roles[AccountRole.DEFERRED_REVENUE] if deferred_unearned else roles[AccountRole.SALES_RETURNS]
        lines = [JournalLine(net_account, debit_irr=net, memo=memo)]
        if vat:
            lines.append(JournalLine(vat_account, debit_irr=vat, memo=memo))
        lines.append(JournalLine(credit_account_id, credit_irr=net + vat, memo=memo))
        return lines
