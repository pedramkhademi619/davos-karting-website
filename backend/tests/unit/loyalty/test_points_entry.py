import uuid
from datetime import UTC, datetime

import pytest

from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.errors.invalid_points_entry_error import InvalidPointsEntryError

K = PointsEntryKind
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def entry(kind: PointsEntryKind, delta: int, **kw: object) -> PointsEntry:
    values = {
        "entry_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "delta": delta,
        "kind": kind,
        "source_ref": "src-1",
        "reason": "r",
        "created_at": NOW,
    }
    return PointsEntry(**{**values, **kw})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kind", "delta"),
    [(K.EARN, 0), (K.EARN, -5), (K.SPEND, 5), (K.EXPIRE, 5), (K.SPEND, 0)],
)
def test_sign_rules_are_enforced_by_kind(kind: PointsEntryKind, delta: int) -> None:
    with pytest.raises(InvalidPointsEntryError):
        entry(kind, delta)


def test_valid_entries() -> None:
    assert entry(K.EARN, 10).delta == 10
    assert entry(K.SPEND, -10).delta == -10
    assert entry(K.REVERSAL, -10, reverses_kind=K.EARN).delta == -10


def test_manual_adjustments_need_a_reason() -> None:
    with pytest.raises(InvalidPointsEntryError):
        entry(K.ADJUST, 5, reason="  ")
    assert entry(K.ADJUST, -5, reason="goodwill correction").delta == -5


def test_reversal_must_name_what_it_reverses() -> None:
    with pytest.raises(InvalidPointsEntryError):
        entry(K.REVERSAL, -5)


def test_every_line_needs_a_source_event_and_only_earns_expire() -> None:
    with pytest.raises(InvalidPointsEntryError):
        entry(K.EARN, 5, source_ref=" ")
    with pytest.raises(InvalidPointsEntryError):
        entry(K.SPEND, -5, expires_at=NOW)


def test_entries_are_immutable() -> None:
    with pytest.raises(AttributeError):
        entry(K.EARN, 5).delta = 999  # type: ignore[misc]
