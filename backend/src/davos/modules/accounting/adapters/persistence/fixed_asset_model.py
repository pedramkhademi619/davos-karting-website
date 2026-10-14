from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class FixedAssetModel(Base):
    __tablename__ = "accounting_fixed_assets"
    __table_args__ = (
        CheckConstraint("cost_irr > 0 AND salvage_irr >= 0 AND salvage_irr < cost_irr", name="cost_valid"),
        CheckConstraint("life_months BETWEEN 1 AND 600", name="life_valid"),
        CheckConstraint("status IN ('active', 'disposed')", name="status_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    asset_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=False)
    cost_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    salvage_irr: Mapped[int] = mapped_column(BigInteger, nullable=False)
    in_service_date: Mapped[date] = mapped_column(Date, nullable=False)
    life_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False)
    note: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
