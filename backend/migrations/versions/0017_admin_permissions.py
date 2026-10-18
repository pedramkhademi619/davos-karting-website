"""Per-account permissions for the admin panel.

``permissions`` is a list of permission keys chosen by the owner; NULL means "the defaults of the role", so every
existing staff account keeps exactly what it could do before, and the owner is never restricted.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: Union[str, Sequence[str], None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("administration_users", sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("administration_users", "permissions")
