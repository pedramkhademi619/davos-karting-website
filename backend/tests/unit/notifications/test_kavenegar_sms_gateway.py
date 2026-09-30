from __future__ import annotations

import logging
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from davos.modules.notifications.adapters.sms.kavenegar_sms_gateway import KavenegarSmsGateway
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.platform.observability.sensitive_data_filter import redact

KEY = "4F3D2C1B0A9988776655443322110FFEEDDCCBBAA"
BASE = f"https://api.kavenegar.com/v1/{KEY}"


def ok(entries: object) -> httpx.Response:
    return httpx.Response(200, json={"return": {"status": 200, "message": "تایید شد"}, "entries": entries})


def failed(status: int, message: str) -> httpx.Response:
    return httpx.Response(status, json={"return": {"status": status, "message": message}, "entries": None})


@pytest.fixture
async def client():
    async with httpx.AsyncClient() as c:
        yield c


def gateway(client: httpx.AsyncClient, **templates: str) -> KavenegarSmsGateway:
    return KavenegarSmsGateway(
        http_client=client,
        api_key=KEY,
        sender="10008663",
        templates=templates,
        base_url="https://api.kavenegar.com/v1",
        timeout_seconds=5.0,
    )


def form(request: httpx.Request) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(request.content.decode()).items()}


@respx.mock
async def test_one_time_codes_use_the_lookup_template_when_one_is_configured(client) -> None:
    route = respx.post(f"{BASE}/verify/lookup.json").mock(
        return_value=ok([{"messageid": 8792343, "receptor": "09121234567"}])
    )
    result = await gateway(client, otp="davos-otp").send(
        SmsMessage(to_local_mobile="09121234567", template_key="otp", parameters={"code": "482913", "ttl_minutes": "2"})
    )
    assert form(route.calls.last.request) == {"receptor": "09121234567", "template": "davos-otp", "token": "482913"}
    assert result.provider_message_id == "8792343"


@respx.mock
async def test_without_a_template_the_persian_text_goes_from_the_sender_line(client) -> None:
    route = respx.post(f"{BASE}/sms/send.json").mock(return_value=ok([{"messageid": 1, "receptor": "09121234567"}]))
    await gateway(client).send(
        SmsMessage(to_local_mobile="09121234567", template_key="otp", parameters={"code": "482913"})
    )
    sent = form(route.calls.last.request)
    assert sent["sender"] == "10008663" and "482913" in sent["message"] and "داوس" in sent["message"]


@respx.mock
async def test_lookup_tokens_never_contain_spaces(client) -> None:
    route = respx.post(f"{BASE}/verify/lookup.json").mock(return_value=ok([{"messageid": 5}]))
    await gateway(client, reservation_confirmed="davos-ticket").send(
        SmsMessage(
            to_local_mobile="09121234567",
            template_key="reservation_confirmed",
            parameters={"ticket": "DK-ABC1234", "date": "۱۴۰۵/۰۷/۰۵", "time": "ساعت ۱۸:۳۰"},
        )
    )
    sent = form(route.calls.last.request)
    assert (sent["token"], sent["token2"]) == ("DK-ABC1234", "۱۴۰۵/۰۷/۰۵") and " " not in sent["token3"]


@respx.mock
async def test_bulk_text_goes_to_a_comma_separated_list(client) -> None:
    route = respx.post(f"{BASE}/sms/send.json").mock(
        return_value=ok([{"messageid": 11, "receptor": "09120000001"}, {"messageid": 12, "receptor": "09120000002"}])
    )
    results = await gateway(client).send_text(["09120000001", "09120000002"], "سلام")
    assert form(route.calls.last.request)["receptor"] == "09120000001,09120000002"
    assert [(r.recipient, r.provider_message_id) for r in results] == [("09120000001", "11"), ("09120000002", "12")]


@respx.mock
async def test_delivery_statuses_are_mapped(client) -> None:
    respx.post(f"{BASE}/sms/status.json").mock(
        return_value=ok(
            [{"messageid": 11, "status": 10}, {"messageid": 12, "status": 14}, {"messageid": 13, "status": 4}]
        )
    )
    statuses = await gateway(client).delivery_statuses(["11", "12", "13"])
    assert statuses == {
        "11": SmsDeliveryStatus.DELIVERED,
        "12": SmsDeliveryStatus.BLOCKED,
        "13": SmsDeliveryStatus.SENT,
    }


@respx.mock
async def test_account_credit(client) -> None:
    respx.post(f"{BASE}/account/info.json").mock(
        return_value=ok({"remaincredit": 1_250_000, "expiredate": 1_800_000_000, "type": "master"})
    )
    info = await gateway(client).account()
    assert info is not None and info.remaining_credit_irr == 1_250_000 and info.expires_at is not None


@pytest.mark.parametrize(("status", "retryable"), [(418, False), (411, False), (403, False), (409, True), (502, True)])
@respx.mock
async def test_provider_errors_say_whether_a_retry_can_help(client, status: int, retryable: bool) -> None:
    respx.post(f"{BASE}/sms/send.json").mock(return_value=failed(status, "خطا"))
    with pytest.raises(SmsProviderError) as info:
        await gateway(client).send_text(["09120000001"], "x")
    assert info.value.retryable is retryable and KEY not in str(info.value)


@respx.mock
async def test_timeouts_are_retryable_and_never_leak_the_key(client) -> None:
    respx.post(f"{BASE}/sms/send.json").mock(side_effect=httpx.ConnectTimeout("slow"))
    with pytest.raises(SmsProviderError) as info:
        await gateway(client).send_text(["09120000001"], "x")
    assert info.value.retryable and KEY not in str(info.value) and info.value.__cause__ is None


@respx.mock
async def test_the_api_key_in_the_url_is_scrubbed_from_logs(client, caplog) -> None:
    respx.post(f"{BASE}/sms/send.json").mock(return_value=ok([{"messageid": 1, "receptor": "09120000001"}]))
    with caplog.at_level(logging.INFO, logger="httpx"):
        await gateway(client).send_text(["09120000001"], "x")
    assert any("api.kavenegar.com" in r.getMessage() for r in caplog.records)  # httpx prints the URL ...
    assert all(KEY not in redact(r.getMessage()) for r in caplog.records)  # ... and the log filter removes the key
    line = f'HTTP Request: POST {BASE}/sms/send.json "HTTP/1.1 200 OK"'
    assert KEY not in redact(line) and "api.kavenegar.com/v1/[redacted]/sms/send.json" in redact(line)
