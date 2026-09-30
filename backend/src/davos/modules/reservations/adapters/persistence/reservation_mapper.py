from __future__ import annotations

from davos.modules.reservations.adapters.persistence.reservation_model import ReservationModel
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.shared_kernel.domain.money import Money


class ReservationMapper:
    @staticmethod
    def to_domain(model: ReservationModel) -> Reservation:
        return Reservation(
            reservation_id=model.id,
            code=model.code,
            customer_id=model.customer_id,
            business_date=model.business_date,
            session_time=model.session_time,
            starts_at=model.starts_at,
            single_count=model.single_count,
            double_count=model.double_count,
            amount=Money(model.amount_irr),
            status=ReservationStatus(model.status),
            source=ReservationSource(model.source),
            contact_name=model.contact_name,
            contact_mobile=model.contact_mobile,
            created_at=model.created_at,
            updated_at=model.updated_at,
            hold_expires_at=model.hold_expires_at,
            confirmed_at=model.confirmed_at,
            payment_ref=model.payment_ref,
            confirmed_late=model.confirmed_late,
            note=model.note,
            cancel_reason=model.cancel_reason,
        )

    @staticmethod
    def to_model(reservation: Reservation) -> ReservationModel:
        return ReservationModel(
            id=reservation.id,
            code=reservation.code,
            customer_id=reservation.customer_id,
            business_date=reservation.business_date,
            session_time=reservation.session_time,
            starts_at=reservation.starts_at,
            single_count=reservation.single_count,
            double_count=reservation.double_count,
            amount_irr=reservation.amount.irr,
            source=reservation.source.value,
            contact_name=reservation.contact_name,
            contact_mobile=reservation.contact_mobile,
            created_at=reservation.created_at,
            note=reservation.note,
            **ReservationMapper.mutable_values(reservation),
        )

    @staticmethod
    def mutable_values(reservation: Reservation) -> dict[str, object]:
        return {
            "status": reservation.status.value,
            "updated_at": reservation.updated_at,
            "hold_expires_at": reservation.hold_expires_at,
            "confirmed_at": reservation.confirmed_at,
            "payment_ref": reservation.payment_ref,
            "confirmed_late": reservation.confirmed_late,
            "cancel_reason": reservation.cancel_reason,
        }
