"""A short, numeric ticket number for each reservation, separate from its uuid id.

The id stays the real primary key and the only thing ever used to look a reservation up (so the ticket number, which
is sequential and read out loud at the counter, can never be used to guess or enumerate someone else's reservation).
``reservations_ticket_number_seq`` (Postgres sequence, starts at 100) hands out the number: ``nextval()`` is atomic
under any concurrency, the same mechanism already used for the payment module's bank order id.

Adding a NOT NULL, UNIQUE column to a table that may already have rows needs three steps: create the sequence, add
the column nullable and backfill every existing row with its own number from the sequence, then add the constraints.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEQUENCE_NAME = "reservations_ticket_number_seq"


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(sa.Sequence(_SEQUENCE_NAME, start=100)))
    op.add_column("reservations", sa.Column("ticket_number", sa.BigInteger(), nullable=True))
    op.execute(
        f"""
        UPDATE reservations
           SET ticket_number = nextval('{_SEQUENCE_NAME}')
         WHERE ticket_number IS NULL
        """
    )
    op.alter_column("reservations", "ticket_number", nullable=False)
    op.create_unique_constraint("uq_reservations_ticket_number", "reservations", ["ticket_number"])


def downgrade() -> None:
    op.drop_constraint("uq_reservations_ticket_number", "reservations", type_="unique")
    op.drop_column("reservations", "ticket_number")
    op.execute(sa.schema.DropSequence(sa.Sequence(_SEQUENCE_NAME)))
