"""booking records and webhook inbox

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-20 20:49:36.807159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('booking_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('external_booking_id', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('amount_irr', sa.BigInteger(), nullable=False),
    sa.Column('session_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_event_id', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('pending', 'confirmed', 'cancelled', 'attended', 'no_show', 'refunded')", name=op.f('ck_booking_records_status_valid')),
    sa.CheckConstraint('amount_irr >= 0', name=op.f('ck_booking_records_amount_not_negative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_booking_records')),
    sa.UniqueConstraint('external_booking_id', name=op.f('uq_booking_records_external_booking_id'))
    )
    op.create_index('ix_booking_records_user_session', 'booking_records', ['user_id', 'session_time'], unique=False)
    op.create_table('booking_webhook_inbox',
    sa.Column('event_id', sa.String(length=100), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('last_error_code', sa.String(length=64), nullable=True),
    sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('received', 'processed', 'failed')", name=op.f('ck_booking_webhook_inbox_status_valid')),
    sa.PrimaryKeyConstraint('event_id', name=op.f('pk_booking_webhook_inbox'))
    )
    op.create_index('ix_booking_inbox_failed', 'booking_webhook_inbox', ['received_at'], unique=False, postgresql_where=sa.text("status = 'failed'"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_booking_inbox_failed', table_name='booking_webhook_inbox', postgresql_where=sa.text("status = 'failed'"))
    op.drop_table('booking_webhook_inbox')
    op.drop_index('ix_booking_records_user_session', table_name='booking_records')
    op.drop_table('booking_records')
