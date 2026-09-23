"""loyalty accounts and append-only points ledger

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "loyalty_accounts",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("customer_id", name=op.f("pk_loyalty_accounts")),
    )
    op.create_table(
        "loyalty_points_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("source_ref", sa.String(length=200), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("reverses_kind", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("delta <> 0", name=op.f("ck_loyalty_points_ledger_delta_not_zero")),
        sa.CheckConstraint(
            "kind IN ('earn', 'spend', 'expire', 'adjust', 'reversal')",
            name=op.f("ck_loyalty_points_ledger_kind_valid"),
        ),
        sa.CheckConstraint("kind <> 'earn' OR delta > 0", name=op.f("ck_loyalty_points_ledger_earn_positive")),
        sa.CheckConstraint(
            "kind NOT IN ('spend', 'expire') OR delta < 0", name=op.f("ck_loyalty_points_ledger_spend_expire_negative")
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["loyalty_accounts.customer_id"],
            name=op.f("fk_loyalty_points_ledger_customer_id_loyalty_accounts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_loyalty_points_ledger")),
        sa.UniqueConstraint("customer_id", "kind", "source_ref", name="uq_loyalty_ledger_source"),
    )
    op.create_index("ix_loyalty_ledger_customer_time", "loyalty_points_ledger", ["customer_id", "created_at"])
    # The ledger is append-only: history can only be corrected with compensating entries.
    op.execute(
        """
        CREATE FUNCTION loyalty_ledger_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'loyalty_points_ledger is append-only (%)', TG_OP USING ERRCODE = 'restrict_violation';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER loyalty_ledger_immutable BEFORE UPDATE OR DELETE ON loyalty_points_ledger "
        "FOR EACH ROW EXECUTE FUNCTION loyalty_ledger_append_only()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS loyalty_ledger_immutable ON loyalty_points_ledger")
    op.execute("DROP FUNCTION IF EXISTS loyalty_ledger_append_only()")
    op.drop_index("ix_loyalty_ledger_customer_time", table_name="loyalty_points_ledger")
    op.drop_table("loyalty_points_ledger")
    op.drop_table("loyalty_accounts")
