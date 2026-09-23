from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from davos.modules.booking.domain.enums.booking_status import BookingStatus
from davos.modules.booking.domain.errors.invalid_booking_event_error import InvalidBookingEventError
from davos.modules.booking.domain.value_objects.booking_event import BookingEvent
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

_MAX_ID = 100


class BookingEventParser:
    """Strict parser for the booking contract. Anything unexpected is rejected, nothing is guessed."""

    def parse(self, body: bytes) -> BookingEvent:
        try:
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError) as exc:
            raise InvalidBookingEventError("بدنه رویداد JSON معتبر نیست.") from exc
        if not isinstance(data, dict):
            raise InvalidBookingEventError("ساختار رویداد معتبر نیست.")
        try:
            return BookingEvent(
                event_id=self._text(data, "event_id"),
                external_booking_id=self._text(data, "external_booking_id"),
                user_id=self._uuid(data, "user_id"),
                status=self._status(data),
                amount=self._amount(data),
                session_time=self._time(data, "session_time"),
                updated_at=self._time(data, "updated_at"),
            )
        except ValidationError as exc:
            raise InvalidBookingEventError(exc.message) from exc

    @staticmethod
    def _text(data: dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_ID:
            raise InvalidBookingEventError(f"فیلد {key} نامعتبر است.")
        return value.strip()

    @staticmethod
    def _uuid(data: dict[str, Any], key: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(data.get(key)))
        except ValueError as exc:
            raise InvalidBookingEventError(f"فیلد {key} نامعتبر است.") from exc

    @staticmethod
    def _status(data: dict[str, Any]) -> BookingStatus:
        try:
            return BookingStatus(str(data.get("status")))
        except ValueError as exc:
            raise InvalidBookingEventError("وضعیت رزرو ناشناخته است.") from exc

    @staticmethod
    def _amount(data: dict[str, Any]) -> Money:
        value = data.get("amount_irr")
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidBookingEventError("مبلغ باید عدد صحیح (ریال) باشد.")
        return Money(value)

    @staticmethod
    def _time(data: dict[str, Any], key: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(str(data.get(key)))
        except ValueError as exc:
            raise InvalidBookingEventError(f"فیلد {key} نامعتبر است.") from exc
        if parsed.tzinfo is None:
            raise InvalidBookingEventError(f"فیلد {key} باید منطقه زمانی داشته باشد.")
        return parsed
