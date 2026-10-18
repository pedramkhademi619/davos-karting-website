from __future__ import annotations

import secrets

from davos.modules.reservations.application.ports.reservation_code_generator import ReservationCodeGenerator

# No 0/O, 1/I/L: the code is read out loud at the counter.
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


class SecureReservationCodeGenerator(ReservationCodeGenerator):
    def new_code(self) -> str:
        return "DK-" + "".join(secrets.choice(_ALPHABET) for _ in range(7))
