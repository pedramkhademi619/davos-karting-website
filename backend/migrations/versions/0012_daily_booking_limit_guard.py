"""Database-level backstop for the owner's optional daily cap on online bookings (people or tickets).

Extends the capacity-guard trigger from 0011 with the same strategy: the application already serialises this check
with a day-wide advisory lock (taken before the per-session lock, so the two can never deadlock) and re-reads the
load under it, but the database enforces it independently too, so the invariant survives a future code path, a
manual query, or a bug that forgets the lock.

The day lock is taken first, before the existing session lock, matching the application's fixed lock order.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "0012"
down_revision: Union[str, Sequence[str], None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PREVIOUS_FUNCTION = """
CREATE OR REPLACE FUNCTION reservations_enforce_online_capacity() RETURNS trigger AS $$
DECLARE
    cap_singles integer;
    cap_doubles integer;
    occ_singles integer;
    occ_doubles integer;
    lock_key text;
BEGIN
    IF NEW.source <> 'online' THEN
        RETURN NEW;
    END IF;
    IF NOT (NEW.status IN ('confirmed', 'attended')
            OR (NEW.status = 'held' AND NEW.hold_expires_at IS NOT NULL AND NEW.hold_expires_at > now())) THEN
        RETURN NEW;
    END IF;

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

_FUNCTION = """
CREATE OR REPLACE FUNCTION reservations_enforce_online_capacity() RETURNS trigger AS $$
DECLARE
    cap_singles integer;
    cap_doubles integer;
    occ_singles integer;
    occ_doubles integer;
    lock_key text;
    daily_mode text;
    daily_limit integer;
    day_tickets integer;
    day_people integer;
BEGIN
    IF NEW.source <> 'online' THEN
        RETURN NEW;
    END IF;
    IF NOT (NEW.status IN ('confirmed', 'attended')
            OR (NEW.status = 'held' AND NEW.hold_expires_at IS NOT NULL AND NEW.hold_expires_at > now())) THEN
        RETURN NEW;
    END IF;

    -- The owner's optional daily cap (people or tickets), off by default. Its lock is taken first, before the
    -- session lock below, matching HoldReservationUseCase's fixed order so the two can never deadlock.
    SELECT data ->> 'daily_booking_limit_mode', NULLIF(data ->> 'daily_booking_limit', '')::int
      INTO daily_mode, daily_limit
      FROM reservations_settings
     WHERE id = 1;
    daily_mode := COALESCE(daily_mode, 'none');

    IF daily_mode <> 'none' AND daily_limit IS NOT NULL THEN
        PERFORM pg_advisory_xact_lock(hashtextextended('reservation-day:' || NEW.business_date::text, 0));

        SELECT COUNT(*), COALESCE(SUM(single_count + 2 * double_count), 0)
          INTO day_tickets, day_people
          FROM reservations
         WHERE business_date = NEW.business_date
           AND source = 'online'
           AND id <> NEW.id
           AND (status IN ('confirmed', 'attended')
                OR (status = 'held' AND hold_expires_at IS NOT NULL AND hold_expires_at > now()));

        IF daily_mode = 'tickets' THEN
            IF day_tickets + 1 > daily_limit THEN
                RAISE EXCEPTION 'daily_booking_limit_reached for %: tickets %/%',
                    NEW.business_date, day_tickets + 1, daily_limit USING ERRCODE = '23514';
            END IF;
        ELSIF daily_mode = 'people' THEN
            IF day_people + NEW.single_count + 2 * NEW.double_count > daily_limit THEN
                RAISE EXCEPTION 'daily_booking_limit_reached for %: people %/%',
                    NEW.business_date, day_people + NEW.single_count + 2 * NEW.double_count, daily_limit
                    USING ERRCODE = '23514';
            END IF;
        END IF;
    END IF;

    -- The existing per-session capacity guard (migration 0011), unchanged below this point.
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


def upgrade() -> None:
    op.execute(_FUNCTION)


def downgrade() -> None:
    op.execute(_PREVIOUS_FUNCTION)
