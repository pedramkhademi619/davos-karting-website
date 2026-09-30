from __future__ import annotations


class GroupSessionPlanner:
    """Fewest sessions for a group, following the owner's rule: every single-seater takes one driver, and a two-seater
    takes two people only when a 4 to 15 year old sits behind a licensed adult. The kart counts are the admin panel's
    booking settings, so a session holds ``singles + children in the rear`` drivers."""

    def __init__(self, *, singles_per_session: int, doubles_per_session: int) -> None:
        self._singles = singles_per_session
        self._doubles = doubles_per_session

    def sessions_needed(self, *, drivers: int, rear_children: int) -> int:
        """``drivers`` includes everyone who drives (single-seaters and the two-seaters' front seats)."""
        singles, doubles = self._singles, self._doubles
        by_children = -(-rear_children // doubles) if doubles else 0
        by_drivers = -(-(drivers - rear_children) // singles) if singles else 0
        return max(by_children, by_drivers, 1)

    def layout(self, *, drivers: int, rear_children: int) -> list[tuple[int, int]]:
        """Per session: (people driving, children in the rear seats), spread as evenly as the rules allow.

        Children are dealt out first (at most one per two-seater), then drivers one by one, starting with the sessions
        that carry a child, so every child's session gets its licensed adult first. With fewer drivers than children
        some child sessions stay without one; the caller must say that an adult has to ride again in those sessions.
        """
        sessions = self.sessions_needed(drivers=drivers, rear_children=rear_children)
        children = [0] * sessions
        for index in range(min(rear_children, sessions * self._doubles)):
            children[index % sessions] += 1
        # each child's two-seater also seats one more driver
        rooms = [self._singles + child for child in children]
        driving = [0] * sessions
        left = min(drivers, sum(rooms))
        while left:
            for index in range(sessions):
                if left and driving[index] < rooms[index]:
                    driving[index] += 1
                    left -= 1
        return list(zip(driving, children, strict=True))
