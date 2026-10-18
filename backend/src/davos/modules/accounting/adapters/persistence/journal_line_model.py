from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class JournalLineModel(Base):
    __tablename__ = "accounting_journal_lines"
    __table_args__ = (
        CheckConstraint("debit_irr >= 0 AND credit_irr >= 0", name="amounts_non_negative"),
        CheckConstraint("(debit_irr = 0) <> (credit_irr = 0)", name="one_side_only"),
        Index("ix_accounting_lines_account", "account_id", "entry_id"),
        Index("ix_accounting_lines_entry", "entry_id"),
        Index("ix_accounting_lines_party", "party_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_journal_entries.id"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=False)
    debit_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    credit_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    memo: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
    party_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
