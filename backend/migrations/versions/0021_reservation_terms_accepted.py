"""Remember when a customer pledged the ages are right and the rules are read.

``reservations.terms_accepted_at``: set when an online booking is held (the booking page makes the tick compulsory, the
API refuses a hold without it). Old rows and counter entries keep NULL.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0021"
down_revision: Union[str, Sequence[str], None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reservations", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reservations", "terms_accepted_at")
