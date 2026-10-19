"""Ticket numbers start again at 100 in every shift.

The number a customer reads out at the track used to come from one global sequence, so a ticket for tomorrow could be
150 and one for the day after 160. Now each business day and shift ("2026-10-19-evening") has its own counter
(``reservation_ticket_counters``) and the first ticket of a shift is 100.

* ``reservations.shift_key``: filled for the existing rows with the default shifts (a session before 15:00 is the
  morning, any other the evening) so old tickets keep their numbers and the counters continue after them.
* the global unique constraint on ``ticket_number`` becomes unique per shift.
* the old sequence stays (demo-data tools and old rows use it); nothing new draws from it.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0020"
down_revision: Union[str, Sequence[str], None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reservation_ticket_counters",
        sa.Column("shift_key", sa.String(length=24), nullable=False),
        sa.Column("last_value", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("shift_key"),
    )
    op.add_column("reservations", sa.Column("shift_key", sa.String(length=24), nullable=True))
    op.execute(
        """
        UPDATE reservations
           SET shift_key = to_char(business_date, 'YYYY-MM-DD') || '-' ||
               CASE WHEN session_time >= TIME '06:00' AND session_time < TIME '15:00' THEN 'morning' ELSE 'evening' END
        """
    )
    op.drop_constraint("uq_reservations_ticket_number", "reservations", type_="unique")
    op.create_unique_constraint("uq_reservations_shift_ticket", "reservations", ["shift_key", "ticket_number"])
    # a shift that already has tickets continues after its highest number (at least 99, so the next one is 100)
    op.execute(
        """
        INSERT INTO reservation_ticket_counters (shift_key, last_value)
        SELECT shift_key, GREATEST(MAX(ticket_number), 99) FROM reservations GROUP BY shift_key
        """
    )


def downgrade() -> None:
    op.drop_constraint("uq_reservations_shift_ticket", "reservations", type_="unique")
    op.create_unique_constraint("uq_reservations_ticket_number", "reservations", ["ticket_number"])
    op.drop_column("reservations", "shift_key")
    op.drop_table("reservation_ticket_counters")
