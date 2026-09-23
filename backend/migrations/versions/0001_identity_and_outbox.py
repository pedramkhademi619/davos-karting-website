"""identity and outbox

Revision ID: 0001
Revises:
Create Date: 2026-09-20 19:52:38.055325

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "identity_otp_challenges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mobile", sa.String(length=16), nullable=False),
        sa.Column("code_digest", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempts >= 0 AND attempts <= max_attempts", name=op.f("ck_identity_otp_challenges_attempts_in_range")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_otp_challenges")),
    )
    op.create_index(
        "ix_identity_otp_challenges_mobile_created", "identity_otp_challenges", ["mobile", "created_at"], unique=False
    )
    op.create_table(
        "identity_users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mobile", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("mobile ~ '^\\+989[0-9]{9}$'", name=op.f("ck_identity_users_mobile_format")),
        sa.CheckConstraint(
            "status IN ('active', 'restricted', 'blocked')", name=op.f("ck_identity_users_status_valid")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_users")),
        sa.UniqueConstraint("mobile", name=op.f("uq_identity_users_mobile")),
    )
    op.create_table(
        "outbox_messages",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("event_name", sa.String(length=200), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk_outbox_messages")),
    )
    op.create_index(
        "ix_outbox_messages_pending",
        "outbox_messages",
        ["available_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )
    op.create_table(
        "identity_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=200), nullable=False),
        sa.Column("ip_hint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["identity_users.id"],
            name=op.f("fk_identity_sessions_user_id_identity_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_sessions")),
        sa.UniqueConstraint("token_digest", name=op.f("uq_identity_sessions_token_digest")),
    )
    op.create_index("ix_identity_sessions_user", "identity_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_identity_sessions_user", table_name="identity_sessions")
    op.drop_table("identity_sessions")
    op.drop_index(
        "ix_outbox_messages_pending", table_name="outbox_messages", postgresql_where=sa.text("published_at IS NULL")
    )
    op.drop_table("outbox_messages")
    op.drop_table("identity_users")
    op.drop_index("ix_identity_otp_challenges_mobile_created", table_name="identity_otp_challenges")
    op.drop_table("identity_otp_challenges")
