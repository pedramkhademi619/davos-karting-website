"""Database-level backstop against overselling a session with online reservations.

The application already serialises holds with a per-session advisory lock and re-reads the load under it, so two
customers racing for the last kart cannot both get it. This migration adds a second, independent guarantee in the
database so the invariant survives a future code path, a manual query, or a bug that forgets the lock:

* A ``BEFORE INSERT OR UPDATE`` trigger on ``reservations`` takes the *same* per-session advisory lock the application
  uses (identical key), so even an unlocked caller is serialised, and then checks that the seats occupied by online
  bookings in that session do not exceed the published capacity.
* Only ``source = 'online'`` rows are held to the capacity. Staff may deliberately overbook walk-ins, which is an
  existing feature, so staff rows are never blocked; an online row is still correctly rejected when staff have filled
  the session.
* "Occupies a seat" matches the application: confirmed or attended, or a hold that has not expired. Capacity is read
  live from the single ``reservations_settings`` row, with the same defaults the domain uses.

The trigger raises SQLSTATE 23514 (check_violation), which SQLAlchemy surfaces as IntegrityError.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FUNCTION = """
CREATE OR REPLACE FUNCTION reservations_enforce_online_capacity() RETURNS trigger AS $$
DECLARE
    cap_singles integer;
    cap_doubles integer;
    occ_singles integer;
    occ_doubles integer;
    lock_key text;
BEGIN
    -- Only online bookings are held to the published capacity; staff may overbook walk-ins on purpose.
    IF NEW.source <> 'online' THEN
        RETURN NEW;
    END IF;
    -- Only a row that actually takes seats can oversell: confirmed/attended, or a hold that has not expired.
    IF NOT (NEW.status IN ('confirmed', 'attended')
            OR (NEW.status = 'held' AND NEW.hold_expires_at IS NOT NULL AND NEW.hold_expires_at > now())) THEN
        RETURN NEW;
    END IF;

    -- The application's per-session lock, re-created here so an unlocked caller is serialised too. Same key string as
    -- SqlAlchemyReservationRepository.lock_session; re-entrant within a transaction that already holds it.
    lock_key := 'reservation-session:' || NEW.business_date::text || ':' || to_char(NEW.session_time, 'HH24:MI');
    PERFORM pg_advisory_xact_lock(hashtextextended(lock_key, 0));

    SELECT COALESCE((data ->> 'single_capacity')::int, 6),
           COALESCE((data ->> 'double_capacity')::int, 1)
      INTO cap_singles, cap_doubles
      FROM reservations_settings
     WHERE id = 1;
    cap_singles := COALESCE(cap_singles, 6);
    cap_doubles := COALESCE(cap_doubles, 1);

    SELECT COALESCE(SUM(single_count), 0), COALESCE(SUM(double_count), 0)
      INTO occ_singles, occ_doubles
      FROM reservations
     WHERE business_date = NEW.business_date
       AND session_time = NEW.session_time
       AND id <> NEW.id
       AND (status IN ('confirmed', 'attended')
            OR (status = 'held' AND hold_expires_at IS NOT NULL AND hold_expires_at > now()));

    occ_singles := occ_singles + NEW.single_count;
    occ_doubles := occ_doubles + NEW.double_count;

    IF occ_singles > cap_singles OR occ_doubles > cap_doubles THEN
        RAISE EXCEPTION
            'session_oversold for % %: online would take singles=%/% doubles=%/%',
            NEW.business_date, to_char(NEW.session_time, 'HH24:MI'),
            occ_singles, cap_singles, occ_doubles, cap_doubles
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGER = """
CREATE TRIGGER trg_reservations_enforce_online_capacity
BEFORE INSERT OR UPDATE OF status, single_count, double_count, hold_expires_at, business_date, session_time, source
ON reservations
FOR EACH ROW EXECUTE FUNCTION reservations_enforce_online_capacity();
"""


def upgrade() -> None:
    op.execute(_FUNCTION)
    op.execute(_TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_reservations_enforce_online_capacity ON reservations")
    op.execute("DROP FUNCTION IF EXISTS reservations_enforce_online_capacity()")
