"""How a counter sale was paid (cash, card reader, transfer), so the accounts can book it to the right place.

Online tickets and seats held without taking money keep the default ``none``.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016"
down_revision: Union[str, Sequence[str], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reservations", sa.Column("payment_method", sa.String(length=12), server_default="none", nullable=False))
    op.create_check_constraint(
        "ck_reservations_payment_method_valid", "reservations", "payment_method IN ('none', 'cash', 'card', 'transfer')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_reservations_payment_method_valid", "reservations", type_="check")
    op.drop_column("reservations", "payment_method")
