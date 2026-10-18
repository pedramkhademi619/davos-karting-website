from __future__ import annotations

from datetime import datetime

import pytest

from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.modules.notifications.application.ports.sms_log_page import SmsLogPage
from davos.modules.notifications.application.ports.sms_log_repository import SmsLogRepository
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.modules.notifications.application.ports.sms_send_result import SmsSendResult
from davos.modules.notifications.application.use_cases.send_bulk_sms_use_case import SendBulkSmsUseCase
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry
from davos.modules.notifications.domain.value_objects.sms_recipient import SmsRecipient
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from tests.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.fakes.fixed_clock import FixedClock


class MemoryLog(SmsLogRepository):
    def __init__(self) -> None:
        self.entries: list[SmsLogEntry] = []

    async def add_many(self, entries: list[SmsLogEntry]) -> None:
        self.entries.extend(entries)

    async def page(self, *, text: str, offset: int, limit: int) -> SmsLogPage:
        return SmsLogPage(items=self.entries[offset : offset + limit], total=len(self.entries))

    async def pending_message_ids(self, *, since: datetime, limit: int) -> list[str]:
        return []

    async def update_statuses(self, statuses: dict[str, SmsDeliveryStatus], now: datetime) -> int:
        return 0


class FlakyGateway(RecordingSmsGateway):
    async def send_text(self, recipients: list[str], text: str) -> list[SmsSendResult]:
        if len(self.texts) == 0:
            self.texts.append((recipients, text))
            raise SmsProviderError("credit", retryable=False)
        return await super().send_text(recipients, text)


def use_case(gateway: RecordingSmsGateway, log: MemoryLog) -> SendBulkSmsUseCase:
    return SendBulkSmsUseCase(uow=FakeUnitOfWork(), gateway=gateway, log=log, clock=FixedClock())


@pytest.mark.parametrize(
    ("raw", "local"),
    [
        ("09121234567", "09121234567"),
        ("+98 912 123 4567", "09121234567"),
        ("۰۹۱۲۱۲۳۴۵۶۷", "09121234567"),
        ("00989121234567", "09121234567"),
        ("9121234567", "09121234567"),
    ],
)
def test_numbers_are_normalised(raw: str, local: str) -> None:
    assert SmsRecipient.parse(raw).local == local


@pytest.mark.parametrize("raw", ["", "0212345678", "0912123456", "abc", "+1 555 1234567"])
def test_non_mobile_numbers_are_refused(raw: str) -> None:
    with pytest.raises(ValidationError):
        SmsRecipient.parse(raw)


async def test_numbers_are_cleaned_deduplicated_and_every_recipient_logged() -> None:
    gateway, log = RecordingSmsGateway(), MemoryLog()
    report = await use_case(gateway, log).execute(
        recipients=["09120000001", "+989120000001", "bad", "09120000002"], text="  سلام  ", sent_by="owner"
    )
    assert report.accepted == 2 and report.invalid_numbers == ["bad"]
    assert gateway.texts == [(["09120000001", "09120000002"], "سلام")]
    assert {e.recipient for e in log.entries} == {"09120000001", "09120000002"}
    assert all(e.batch_id == report.batch_id and e.sent_by == "owner" for e in log.entries)


async def test_large_lists_go_out_in_chunks_of_one_hundred() -> None:
    gateway, log = RecordingSmsGateway(), MemoryLog()
    numbers = [f"0912{i:07d}" for i in range(250)]
    report = await use_case(gateway, log).execute(recipients=numbers, text="x", sent_by="owner")
    assert [len(chunk) for chunk, _ in gateway.texts] == [100, 100, 50] and report.accepted == 250


async def test_a_refused_chunk_is_logged_as_failed_and_the_rest_still_go_out() -> None:
    gateway, log = FlakyGateway(), MemoryLog()
    numbers = [f"0912{i:07d}" for i in range(150)]
    report = await use_case(gateway, log).execute(recipients=numbers, text="x", sent_by="owner")
    assert (report.accepted, report.failed) == (50, 100)
    assert sum(e.status is SmsDeliveryStatus.FAILED for e in log.entries) == 100


@pytest.mark.parametrize(("numbers", "text"), [(["09120000001"], "   "), (["x"], "hi"), (["09120000001"], "ا" * 601)])
async def test_empty_or_oversized_messages_are_refused(numbers: list[str], text: str) -> None:
    with pytest.raises(ValidationError):
        await use_case(RecordingSmsGateway(), MemoryLog()).execute(recipients=numbers, text=text, sent_by="owner")
