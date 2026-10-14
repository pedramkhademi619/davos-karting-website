from __future__ import annotations

from davos.modules.reservations.domain.enums.daily_booking_limit_mode import DailyBookingLimitMode
from davos.modules.reservations.domain.errors.daily_booking_limit_reached_error import DailyBookingLimitReachedError
from davos.modules.reservations.domain.value_objects.daily_online_load import DailyOnlineLoad
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings


class DailyBookingLimit:
    """The owner's optional cap on today's online bookings (off by default), checked against one new request.

    The cap counts people, tickets, or both (then whichever is reached first stops online booking). It leaves room for
    walk-in customers: once reached, online booking refuses new holds for the rest of the business day, but the counter
    can keep selling (staff entries carry ``source="staff"`` and are never counted).
    """

    def __init__(self, settings: ScheduleSettings) -> None:
        self._settings = settings

    def check(self, load: DailyOnlineLoad, single_count: int, double_count: int) -> None:
        mode = self._settings.daily_booking_limit_mode
        tickets = self._settings.daily_ticket_limit
        people = self._settings.daily_people_limit
        counts_tickets = mode in (DailyBookingLimitMode.TICKETS, DailyBookingLimitMode.BOTH) and tickets is not None
        counts_people = mode in (DailyBookingLimitMode.PEOPLE, DailyBookingLimitMode.BOTH) and people is not None
        if counts_tickets and tickets is not None and load.tickets + 1 > tickets:
            raise DailyBookingLimitReachedError(DailyBookingLimitMode.TICKETS, tickets)
        if counts_people and people is not None and load.people + single_count + 2 * double_count > people:
            raise DailyBookingLimitReachedError(DailyBookingLimitMode.PEOPLE, people)
