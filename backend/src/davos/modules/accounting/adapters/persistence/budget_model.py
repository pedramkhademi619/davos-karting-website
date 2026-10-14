from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class BudgetModel(Base):
    __tablename__ = "accounting_budgets"
    __table_args__ = (CheckConstraint("month BETWEEN 1 AND 12 AND amount_irr > 0", name="valid"),)

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_accounts.id"), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
