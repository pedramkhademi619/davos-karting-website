from __future__ import annotations

from davos.modules.reservations.domain.errors.session_full_error import SessionFullError
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.modules.reservations.domain.value_objects.session_load import SessionLoad
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class SeatAllocator:
    """Checks a request for karts against what is left in one session."""

    def __init__(self, settings: ScheduleSettings) -> None:
        self._settings = settings

    def remaining(self, load: SessionLoad) -> SessionLoad:
        return SessionLoad(
            singles=max(self._settings.single_capacity - load.singles, 0),
            doubles=max(self._settings.double_capacity - load.doubles, 0),
        )

    def check(self, load: SessionLoad, single_count: int, double_count: int) -> None:
        if single_count < 0 or double_count < 0 or single_count + double_count == 0:
            raise ValidationError("حداقل یک خودرو انتخاب کنید.", code="no_karts_selected")
        if single_count + double_count > self._settings.max_karts_per_reservation:
            raise ValidationError(
                f"در هر رزرو حداکثر {self._settings.max_karts_per_reservation} خودرو می‌توانید انتخاب کنید.",
                code="too_many_karts",
            )
        left = self.remaining(load)
        if single_count > left.singles or double_count > left.doubles:
            raise SessionFullError(left.singles, left.doubles)
