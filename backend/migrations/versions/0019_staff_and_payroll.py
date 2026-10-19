"""Staff members and what they are paid (accounting module).

A payment is booked as a payroll expense in the journal; ``entry_id`` links the two. Only new tables, so older code keeps
working (expand step).
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: Union[str, Sequence[str], None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounting_staff",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=80), server_default="", nullable=False),
        sa.Column("mobile", sa.String(length=20), server_default="", nullable=False),
        sa.Column("monthly_salary_irr", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("note", sa.String(length=300), server_default="", nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "accounting_staff_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=12), nullable=False),
        sa.Column("amount_irr", sa.BigInteger(), nullable=False),
        sa.Column("month_key", sa.String(length=7), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=300), server_default="", nullable=False),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["staff_id"], ["accounting_staff.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounting_staff_payments_staff_id", "accounting_staff_payments", ["staff_id"])
    op.create_index("ix_accounting_staff_payments_month_key", "accounting_staff_payments", ["month_key"])


def downgrade() -> None:
    op.drop_index("ix_accounting_staff_payments_month_key", table_name="accounting_staff_payments")
    op.drop_index("ix_accounting_staff_payments_staff_id", table_name="accounting_staff_payments")
    op.drop_table("accounting_staff_payments")
    op.drop_table("accounting_staff")
