"""assistant knowledge base and interactions

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-20 20:00:10.800183

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Trigram matching backs Persian FAQ retrieval (KnowledgeSearchPort). Needs a UTF-8 database.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "assistant_interactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("source_entry_ids", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("helpful", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_interactions")),
    )
    op.create_index(
        "ix_assistant_interactions_conversation", "assistant_interactions", ["conversation_id"], unique=False
    )
    op.create_index(
        "ix_assistant_interactions_outcome_time", "assistant_interactions", ["outcome", "occurred_at"], unique=False
    )
    op.create_index("ix_assistant_interactions_retention", "assistant_interactions", ["retention_until"], unique=False)
    op.create_table(
        "assistant_knowledge_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_ref", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=300), nullable=False),
        sa.Column("title_norm", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_type IN ('faq', 'policy', 'service', 'pricing', 'contact')",
            name=op.f("ck_assistant_knowledge_entries_source_type_valid"),
        ),
        sa.CheckConstraint(
            "url LIKE '/%' AND url NOT LIKE '//%'", name=op.f("ck_assistant_knowledge_entries_url_is_internal_path")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_knowledge_entries")),
        sa.UniqueConstraint("source_type", "source_ref", name="uq_assistant_knowledge_source"),
    )
    op.create_index(
        "ix_assistant_knowledge_search_text_trgm",
        "assistant_knowledge_entries",
        ["search_text"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_assistant_knowledge_title_trgm",
        "assistant_knowledge_entries",
        ["title_norm"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title_norm": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_assistant_knowledge_title_trgm",
        table_name="assistant_knowledge_entries",
        postgresql_using="gin",
        postgresql_ops={"title_norm": "gin_trgm_ops"},
    )
    op.drop_index(
        "ix_assistant_knowledge_search_text_trgm",
        table_name="assistant_knowledge_entries",
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )
    op.drop_table("assistant_knowledge_entries")
    op.drop_index("ix_assistant_interactions_retention", table_name="assistant_interactions")
    op.drop_index("ix_assistant_interactions_outcome_time", table_name="assistant_interactions")
    op.drop_index("ix_assistant_interactions_conversation", table_name="assistant_interactions")
    op.drop_table("assistant_interactions")
