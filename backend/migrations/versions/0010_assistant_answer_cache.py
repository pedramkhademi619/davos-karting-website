"""assistant answer cache: stored answers found by meaning (pgvector), and which stored answer a reply came from

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, Sequence[str], None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "assistant_answer_cache",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("original_query", sa.Text(), nullable=False),
        sa.Column("resolved_query", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), server_default="", nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("hit_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_answer_cache")),
    )
    op.create_index(
        "ix_assistant_answer_cache_fingerprint_active", "assistant_answer_cache", ["fingerprint", "is_active"]
    )
    op.add_column("assistant_interactions", sa.Column("cache_entry_id", sa.UUID(), nullable=True))
    op.add_column(
        "assistant_interactions",
        sa.Column("served_from_cache", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("assistant_interactions", "served_from_cache")
    op.drop_column("assistant_interactions", "cache_entry_id")
    op.drop_index("ix_assistant_answer_cache_fingerprint_active", table_name="assistant_answer_cache")
    op.drop_table("assistant_answer_cache")
