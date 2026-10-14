from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class DepreciationRunModel(Base):
    """One asset's depreciation for one Jalali month; the primary key makes a month run at most once per asset."""

    __tablename__ = "accounting_depreciation_runs"

    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_fixed_assets.id"), primary_key=True)
    month_key: Mapped[str] = mapped_column(String(7), primary_key=True)
    amount_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_journal_entries.id"), nullable=False)
