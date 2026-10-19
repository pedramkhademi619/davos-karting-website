from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class StaffMemberModel(Base):
    __tablename__ = "accounting_staff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    mobile: Mapped[str] = mapped_column(String(20), nullable=False, server_default="")
    monthly_salary_irr: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    note: Mapped[str] = mapped_column(String(300), nullable=False, server_default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
