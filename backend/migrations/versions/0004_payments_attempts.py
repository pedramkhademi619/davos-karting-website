"""payments attempts

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-20 20:37:45.979756

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "payments_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_ref", sa.String(length=100), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("amount_irr", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("authority", sa.String(length=64), nullable=True),
        sa.Column("reference_id", sa.String(length=64), nullable=True),
        sa.Column("failure_reason", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status <> 'paid' OR reference_id IS NOT NULL", name=op.f("ck_payments_attempts_paid_has_reference")
        ),
        sa.CheckConstraint(
            "status IN ('created', 'redirected', 'verifying', 'unknown', 'paid', 'failed', 'expired')",
            name=op.f("ck_payments_attempts_status_valid"),
        ),
        sa.CheckConstraint("amount_irr > 0", name=op.f("ck_payments_attempts_amount_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments_attempts")),
        sa.UniqueConstraint("authority", name=op.f("uq_payments_attempts_authority")),
    )
    op.create_index("ix_payments_customer", "payments_attempts", ["customer_id", "created_at"], unique=False)
    op.create_index("ix_payments_status_updated", "payments_attempts", ["status", "updated_at"], unique=False)
    op.create_index(
        "uq_payments_one_paid_per_order",
        "payments_attempts",
        ["order_ref"],
        unique=True,
        postgresql_where=sa.text("status = 'paid'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_payments_one_paid_per_order", table_name="payments_attempts", postgresql_where=sa.text("status = 'paid'")
    )
    op.drop_index("ix_payments_status_updated", table_name="payments_attempts")
    op.drop_index("ix_payments_customer", table_name="payments_attempts")
    op.drop_table("payments_attempts")
