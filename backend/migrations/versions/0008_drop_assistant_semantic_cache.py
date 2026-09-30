"""drop assistant semantic cache (the local embedding model was retired; too much CPU/RAM pressure hurt normal answers)

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-23 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 768


def upgrade() -> None:
    """Undo everything 0007 added, except the `vector` extension itself (it belongs to the database, like pg_trgm)."""
    op.drop_column("assistant_interactions", "served_from_cache")
    op.drop_column("assistant_interactions", "cache_entry_id")
    op.drop_index("ix_assistant_semantic_cache_last_used", table_name="assistant_semantic_cache")
    op.drop_index("ix_assistant_semantic_cache_fingerprint_active", table_name="assistant_semantic_cache")
    op.drop_index(
        "ix_assistant_semantic_cache_embedding_hnsw",
        table_name="assistant_semantic_cache",
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.drop_table("assistant_semantic_cache")


def downgrade() -> None:
    """Recreate exactly what 0007 created (kept here, rather than re-running 0007, so `downgrade base` / `upgrade head`
    round-trips cleanly: an already-downgraded-past-0008 database re-runs this body on its way back up to head)."""
    op.create_table(
        "assistant_semantic_cache",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("original_query", sa.Text(), nullable=False),
        sa.Column("resolved_query", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), server_default="", nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("hit_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_flagged_for_review", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_semantic_cache")),
    )
    op.create_index(
        "ix_assistant_semantic_cache_embedding_hnsw",
        "assistant_semantic_cache",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_assistant_semantic_cache_fingerprint_active",
        "assistant_semantic_cache",
        ["fingerprint", "is_active"],
        unique=False,
    )
    op.create_index("ix_assistant_semantic_cache_last_used", "assistant_semantic_cache", ["last_used_at"], unique=False)
    op.add_column("assistant_interactions", sa.Column("cache_entry_id", sa.UUID(), nullable=True))
    op.add_column(
        "assistant_interactions",
        sa.Column("served_from_cache", sa.Boolean(), server_default="false", nullable=False),
    )
