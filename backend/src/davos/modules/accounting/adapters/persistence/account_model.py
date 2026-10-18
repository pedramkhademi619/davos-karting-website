from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from davos.platform.persistence.base import Base


class AccountModel(Base):
    __tablename__ = "accounting_accounts"
    __table_args__ = (
        CheckConstraint("type IN ('asset', 'liability', 'equity', 'revenue', 'expense')", name="type_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("accounting_accounts.id"))
    is_group: Mapped[bool] = mapped_column(Boolean, nullable=False)
    role: Mapped[str | None] = mapped_column(String(32), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
