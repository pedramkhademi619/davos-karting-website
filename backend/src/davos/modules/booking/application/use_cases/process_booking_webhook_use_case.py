from __future__ import annotations

from davos.modules.booking.application.services.booking_event_processor import BookingEventProcessor
from davos.modules.booking.application.services.webhook_outcome import WebhookOutcome
from davos.modules.booking.domain.errors.booking_integration_disabled_error import BookingIntegrationDisabledError
from davos.modules.booking.domain.services.booking_event_parser import BookingEventParser
from davos.modules.booking.domain.services.webhook_signature_verifier import WebhookSignatureVerifier
from davos.shared_kernel.application.clock import Clock


class ProcessBookingWebhookUseCase:
    """Entry point for the booking system's webhook. Order matters: flag -> signature -> parse -> apply."""

    def __init__(
        self,
        *,
        enabled: bool,
        verifier: WebhookSignatureVerifier,
        parser: BookingEventParser,
        processor: BookingEventProcessor,
        clock: Clock,
    ) -> None:
        self._enabled = enabled
        self._verifier = verifier
        self._parser = parser
        self._processor = processor
        self._clock = clock

    async def execute(self, *, raw_body: bytes, signature_header: str) -> WebhookOutcome:
        if not self._enabled:
            raise BookingIntegrationDisabledError
        self._verifier.verify(signature_header, raw_body, self._clock.now())  # nothing unsigned is even parsed
        event = self._parser.parse(raw_body)
        return await self._processor.process(event, raw_body.decode("utf-8"))
