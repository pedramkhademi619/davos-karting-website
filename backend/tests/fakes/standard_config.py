"""Standard configuration for tests, built the way production builds it: from AppSettings' own defaults (never a
developer's .env) through PolicyFactory, and from the admin panel's initial settings. Tests change one value with
``dataclasses.replace`` instead of repeating numbers that already live in AppSettings."""

from __future__ import annotations

from dataclasses import replace

from davos.composition.adapters.schedule_booking_facts import ScheduleBookingFacts
from davos.composition.policy_factory import PolicyFactory
from davos.modules.administration.domain.value_objects.admin_security_policy import AdminSecurityPolicy
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.platform.settings.app_settings import AppSettings

DEFAULT_SETTINGS = AppSettings(_env_file=None)  # type: ignore[call-arg]
TEST_CONTACT_PHONE = "09120000000"


def otp_policy(**changes: object) -> OtpPolicy:
    return replace(PolicyFactory.otp(DEFAULT_SETTINGS), **changes)  # type: ignore[arg-type]


def otp_limits(**changes: object) -> OtpRateLimitPolicy:
    return replace(PolicyFactory.otp_limits(DEFAULT_SETTINGS), **changes)  # type: ignore[arg-type]


def admin_security(**changes: object) -> AdminSecurityPolicy:
    return replace(PolicyFactory.admin_security(DEFAULT_SETTINGS), **changes)  # type: ignore[arg-type]


def assistant_policy(**changes: object) -> AssistantPolicy:
    return replace(PolicyFactory.assistant(DEFAULT_SETTINGS), **changes)  # type: ignore[arg-type]


def booking_facts(**changes: object) -> BookingFacts:
    """The admin panel's initial booking settings as the assistant sees them."""
    facts = ScheduleBookingFacts.from_settings(ScheduleSettings(), contact_phone=TEST_CONTACT_PHONE)
    return replace(facts, **changes)  # type: ignore[arg-type]
