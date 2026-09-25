from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.errors.invalid_reservation_transition_error import (
    InvalidReservationTransitionError,
)
from davos.modules.reservations.domain.events.reservation_cancelled import ReservationCancelled
from davos.modules.reservations.domain.events.reservation_confirmed import ReservationConfirmed
from davos.shared_kernel.domain.aggregate_root import AggregateRoot
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

S = ReservationStatus


class Reservation(AggregateRoot[uuid.UUID]):
    """Karts reserved in one session: a ticket, like a cinema seat.

    Online reservations start HELD (the seats are taken while the customer pays) and become CONFIRMED when the payment
    is verified. A payment that arrives after the hold ran out still confirms the reservation (the customer has paid)
    and is flagged ``confirmed_late`` so staff can check the session.
    """

    def __init__(
        self,
        *,
        reservation_id: uuid.UUID,
        code: str,
        customer_id: uuid.UUID | None,
        business_date: date,
        session_time: time,
        starts_at: datetime,
        single_count: int,
        double_count: int,
        amount: Money,
        status: ReservationStatus,
        source: ReservationSource,
        contact_name: str,
        contact_mobile: str,
        created_at: datetime,
        updated_at: datetime,
        hold_expires_at: datetime | None = None,
        confirmed_at: datetime | None = None,
        payment_ref: str | None = None,
        confirmed_late: bool = False,
        note: str = "",
        cancel_reason: str = "",
    ) -> None:
        super().__init__(reservation_id)
        self.code = code
        self.customer_id = customer_id
        self.business_date = business_date
        self.session_time = session_time
        self.starts_at = starts_at
        self.single_count = single_count
        self.double_count = double_count
        self.amount = amount
        self.status = status
        self.source = source
        self.contact_name = contact_name
        self.contact_mobile = contact_mobile
        self.created_at = created_at
        self.updated_at = updated_at
        self.hold_expires_at = hold_expires_at
        self.confirmed_at = confirmed_at
        self.payment_ref = payment_ref
        self.confirmed_late = confirmed_late
        self.note = note
        self.cancel_reason = cancel_reason

    @classmethod
    def hold(
        cls,
        *,
        code: str,
        customer_id: uuid.UUID,
        business_date: date,
        session_time: time,
        starts_at: datetime,
        single_count: int,
        double_count: int,
        amount: Money,
        contact_name: str,
        contact_mobile: str,
        now: datetime,
        hold_minutes: int,
    ) -> Reservation:
        cls._check_counts(single_count, double_count)
        if amount.irr <= 0:
            raise ValidationError("مبلغ رزرو باید بیشتر از صفر باشد.", code="reservation_amount_not_positive")
        return cls(
            reservation_id=uuid.uuid4(),
            code=code,
            customer_id=customer_id,
            business_date=business_date,
            session_time=session_time,
            starts_at=starts_at,
            single_count=single_count,
            double_count=double_count,
            amount=amount,
            status=S.HELD,
            source=ReservationSource.ONLINE,
            contact_name=cls._clean_name(contact_name),
            contact_mobile=contact_mobile,
            created_at=now,
            updated_at=now,
            hold_expires_at=now + timedelta(minutes=hold_minutes),
        )

    @classmethod
    def staff_entry(
        cls,
        *,
        code: str,
        business_date: date,
        session_time: time,
        starts_at: datetime,
        single_count: int,
        double_count: int,
        amount: Money,
        contact_name: str,
        contact_mobile: str,
        note: str,
        now: datetime,
    ) -> Reservation:
        """Seats sold or promised at the counter, entered so the website does not sell them again."""
        cls._check_counts(single_count, double_count)
        reservation = cls(
            reservation_id=uuid.uuid4(),
            code=code,
            customer_id=None,
            business_date=business_date,
            session_time=session_time,
            starts_at=starts_at,
            single_count=single_count,
            double_count=double_count,
            amount=amount,
            status=S.CONFIRMED,
            source=ReservationSource.STAFF,
            contact_name=cls._clean_name(contact_name),
            contact_mobile=contact_mobile,
            created_at=now,
            updated_at=now,
            confirmed_at=now,
            note=note.strip()[:500],
        )
        reservation._raise_confirmed(now)
        return reservation

    @property
    def people(self) -> int:
        return self.single_count + 2 * self.double_count

    def occupies_seats_at(self, now: datetime) -> bool:
        if self.status in {S.CONFIRMED, S.ATTENDED}:
            return True
        return self.status is S.HELD and self.hold_expires_at is not None and now < self.hold_expires_at

    def confirm_payment(self, payment_ref: str, now: datetime) -> bool:
        """Confirm after a verified payment. Returns False when it was already confirmed (idempotent)."""
        if self.status in {S.CONFIRMED, S.ATTENDED} and self.payment_ref == payment_ref:
            return False
        if self.status not in {S.HELD, S.EXPIRED}:
            raise InvalidReservationTransitionError(self.status.value, S.CONFIRMED.value)
        self.confirmed_late = (
            self.confirmed_late
            or self.status is S.EXPIRED
            or (self.hold_expires_at is not None and now >= self.hold_expires_at)
        )
        self.status = S.CONFIRMED
        self.payment_ref = payment_ref
        self.confirmed_at = now
        self.updated_at = now
        self._raise_confirmed(now)
        return True

    def renew_hold(self, now: datetime, minutes: int) -> None:
        """A payment arrived after the hold ran out and the karts are still free: take them again until recorded."""
        if self.status not in {S.HELD, S.EXPIRED}:
            raise InvalidReservationTransitionError(self.status.value, S.HELD.value)
        self.status = S.HELD
        self.hold_expires_at = now + timedelta(minutes=minutes)
        self.confirmed_late = True
        self.updated_at = now

    def expire(self, now: datetime) -> None:
        if self.status is not S.HELD or self.hold_expires_at is None or now < self.hold_expires_at:
            raise InvalidReservationTransitionError(self.status.value, S.EXPIRED.value)
        self.status = S.EXPIRED
        self.updated_at = now

    def cancel(self, *, reason: str, by_staff: bool, now: datetime) -> None:
        allowed = {S.HELD, S.CONFIRMED} if by_staff else {S.HELD}
        if self.status not in allowed:
            raise InvalidReservationTransitionError(self.status.value, S.CANCELLED.value)
        was_paid = self.status is S.CONFIRMED and self.payment_ref is not None
        self.status = S.CANCELLED
        self.cancel_reason = reason.strip()[:300]
        self.updated_at = now
        self._raise(
            ReservationCancelled(
                reservation_id=self.id,
                customer_id=self.customer_id,
                code=self.code,
                starts_at=self.starts_at,
                was_paid=was_paid,
                reason=self.cancel_reason,
                occurred_at=now,
            )
        )

    def mark_attended(self, now: datetime) -> None:
        if self.status is not S.CONFIRMED:
            raise InvalidReservationTransitionError(self.status.value, S.ATTENDED.value)
        self.status = S.ATTENDED
        self.updated_at = now

    def _raise_confirmed(self, now: datetime) -> None:
        self._raise(
            ReservationConfirmed(
                reservation_id=self.id,
                customer_id=self.customer_id,
                code=self.code,
                starts_at=self.starts_at,
                single_count=self.single_count,
                double_count=self.double_count,
                amount_irr=self.amount.irr,
                source=self.source.value,
                confirmed_late=self.confirmed_late,
                occurred_at=now,
            )
        )

    @staticmethod
    def _check_counts(single_count: int, double_count: int) -> None:
        if single_count < 0 or double_count < 0 or single_count + double_count == 0:
            raise ValidationError("حداقل یک خودرو انتخاب کنید.", code="no_karts_selected")

    @staticmethod
    def _clean_name(name: str) -> str:
        return " ".join(name.split())[:80]
