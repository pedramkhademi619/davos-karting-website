"""outbox dead-letter tracking

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Expand step (backward compatible): nullable column, then a narrower partial index."""
    op.add_column("outbox_messages", sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_index("ix_outbox_messages_pending", table_name="outbox_messages")
    op.create_index(
        "ix_outbox_messages_pending",
        "outbox_messages",
        ["available_at"],
        postgresql_where=sa.text("published_at IS NULL AND dead_lettered_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_messages_pending", table_name="outbox_messages")
    op.create_index(
        "ix_outbox_messages_pending",
        "outbox_messages",
        ["available_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.drop_column("outbox_messages", "dead_lettered_at")
