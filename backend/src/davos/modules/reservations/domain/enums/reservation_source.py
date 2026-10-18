from enum import StrEnum


class ReservationSource(StrEnum):
    ONLINE = "online"  # booked and paid by the customer on the website
    STAFF = "staff"  # entered by staff (for example to block seats sold at the counter)
