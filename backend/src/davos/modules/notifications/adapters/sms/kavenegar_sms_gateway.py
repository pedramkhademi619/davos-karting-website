from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from davos.modules.notifications.adapters.sms.sms_text_templates import render
from davos.modules.notifications.application.ports.sms_account_info import SmsAccountInfo
from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.modules.notifications.application.ports.sms_send_result import SmsSendResult
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus

logger = logging.getLogger(__name__)

# Which message parameters fill Kavenegar's lookup tokens (token, token2, token3), per template key.
_LOOKUP_TOKENS: dict[str, tuple[str, ...]] = {
    "otp": ("code",),
    "reservation_confirmed": ("ticket", "date", "time"),
}
# Kavenegar answers these HTTP statuses when trying again later can help.
_RETRYABLE = {409, 429, 500, 502, 503, 504}
_STATUS_BY_CODE = {
    1: SmsDeliveryStatus.QUEUED,
    2: SmsDeliveryStatus.QUEUED,
    4: SmsDeliveryStatus.SENT,
    5: SmsDeliveryStatus.SENT,
    6: SmsDeliveryStatus.FAILED,
    10: SmsDeliveryStatus.DELIVERED,
    11: SmsDeliveryStatus.FAILED,
    13: SmsDeliveryStatus.FAILED,
    14: SmsDeliveryStatus.BLOCKED,
    100: SmsDeliveryStatus.UNKNOWN,
}


class KavenegarSmsGateway(SmsGatewayPort):
    """Kavenegar REST API (https://kavenegar.com/rest.html).

    One-time codes and booking confirmations use ``verify/lookup`` with a template approved in the Kavenegar panel
    when one is configured (fast service line, not affected by promotional blocks); otherwise the text is sent with
    ``sms/send`` from the configured sender line. Staff messages always use ``sms/send``.

    The API key is part of the URL path, so every log line is scrubbed by the logging filter, and exceptions raised
    from here never include the URL.
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient,
        api_key: str,
        sender: str,
        templates: dict[str, str],
        base_url: str = "https://api.kavenegar.com/v1",
        timeout_seconds: float = 10.0,
    ) -> None:
        self._client = http_client
        self._api_key = api_key
        self._sender = sender
        self._templates = {k: v for k, v in templates.items() if v}
        self._base = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    async def send(self, message: SmsMessage) -> SmsSendResult:
        template = self._templates.get(message.template_key)
        tokens = _LOOKUP_TOKENS.get(message.template_key)
        if template and tokens:
            data = {"receptor": message.to_local_mobile, "template": template}
            for index, name in enumerate(tokens):
                key = "token" if index == 0 else f"token{index + 1}"
                data[key] = self._token(message.parameters.get(name, "-"))
            entries = await self._post("verify/lookup.json", data)
        else:
            entries = await self._post(
                "sms/send.json",
                {
                    "receptor": message.to_local_mobile,
                    "sender": self._sender,
                    "message": render(message.template_key, message.parameters),
                },
            )
        return self._results(entries)[0]

    async def send_text(self, recipients: list[str], text: str) -> list[SmsSendResult]:
        if not recipients:
            return []
        entries = await self._post(
            "sms/send.json", {"receptor": ",".join(recipients[:100]), "sender": self._sender, "message": text}
        )
        return self._results(entries)

    async def delivery_statuses(self, message_ids: list[str]) -> dict[str, SmsDeliveryStatus]:
        if not message_ids:
            return {}
        entries = await self._post("sms/status.json", {"messageid": ",".join(message_ids[:500])})
        statuses: dict[str, SmsDeliveryStatus] = {}
        for entry in entries:
            if isinstance(entry, dict) and "messageid" in entry:
                code = entry.get("status")
                statuses[str(entry["messageid"])] = _STATUS_BY_CODE.get(
                    int(code) if isinstance(code, int | str) and str(code).isdigit() else -1,
                    SmsDeliveryStatus.UNKNOWN,
                )
        return statuses

    async def account(self) -> SmsAccountInfo | None:
        entries = await self._post("account/info.json", {})
        info = entries if isinstance(entries, dict) else (entries[0] if entries else {})
        if not isinstance(info, dict):
            raise SmsProviderError("پاسخ کاوه‌نگار نامفهوم است", retryable=True)
        expires = info.get("expiredate")
        return SmsAccountInfo(
            remaining_credit_irr=int(info.get("remaincredit") or 0),
            expires_at=datetime.fromtimestamp(int(expires), tz=UTC) if expires else None,
            account_type=str(info.get("type") or ""),
        )

    async def _post(self, method: str, data: dict[str, str]) -> Any:
        url = f"{self._base}/{self._api_key}/{method}"
        try:
            response = await self._client.post(url, data=data, timeout=self._timeout)
        except httpx.TimeoutException:
            raise SmsProviderError("کاوه‌نگار در زمان مقرر پاسخ نداد", retryable=True) from None
        except httpx.TransportError:
            raise SmsProviderError("ارتباط با کاوه‌نگار برقرار نشد", retryable=True) from None
        try:
            payload = response.json()
        except ValueError:
            raise SmsProviderError(f"پاسخ نامفهوم از کاوه‌نگار (HTTP {response.status_code})", retryable=True) from None
        status = payload.get("return", {}).get("status") if isinstance(payload, dict) else None
        if response.status_code != 200 or status != 200:
            message = payload.get("return", {}).get("message", "") if isinstance(payload, dict) else ""
            code = status if isinstance(status, int) else response.status_code
            raise SmsProviderError(f"کاوه‌نگار: {code} {message}".strip()[:200], retryable=code in _RETRYABLE)
        return payload.get("entries", [])

    @staticmethod
    def _results(entries: Any) -> list[SmsSendResult]:
        results = [
            SmsSendResult(provider_message_id=str(e["messageid"]), recipient=str(e.get("receptor", "")))
            for e in (entries if isinstance(entries, list) else [])
            if isinstance(e, dict) and e.get("messageid") is not None
        ]
        if not results:
            raise SmsProviderError("کاوه‌نگار پیامی ثبت نکرد", retryable=False)
        return results

    @staticmethod
    def _token(value: str) -> str:
        """Lookup tokens may not contain spaces."""
        return "‌".join(str(value).split())[:100] or "-"
