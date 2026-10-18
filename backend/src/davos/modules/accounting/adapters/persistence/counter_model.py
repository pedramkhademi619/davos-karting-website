from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class CounterModel(Base):
    """Gapless counters (one row per fiscal year's document numbers). A row lock serialises its users."""

    __tablename__ = "accounting_counters"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[int] = mapped_column(BigInteger, nullable=False)
