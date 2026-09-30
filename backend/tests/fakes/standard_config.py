"""Standard configuration for tests, built the way production builds it: the settings from the repository's
.env.example (never a developer's .env, so results do not depend on the machine) through PolicyFactory, and the
admin panel's initial settings. Tests change one value with keyword overrides or ``dataclasses.replace`` instead of
repeating numbers that already live in .env.example."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from dotenv import dotenv_values

from davos.composition.adapters.schedule_booking_facts import ScheduleBookingFacts
from davos.composition.policy_factory import PolicyFactory
from davos.modules.administration.domain.value_objects.admin_security_policy import AdminSecurityPolicy
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.platform.settings.app_settings import AppSettings

EXAMPLE_ENV = Path(__file__).resolve().parents[3] / ".env.example"


def example_settings(**overrides: object) -> AppSettings:
    """The complete development configuration from .env.example, with ``overrides`` applied."""
    return AppSettings(_env_file=EXAMPLE_ENV, **overrides)  # type: ignore[arg-type]


def example_environment() -> dict[str, str]:
    """.env.example as environment variables, the way docker-compose hands .env to the containers."""
    return {name: value or "" for name, value in dotenv_values(EXAMPLE_ENV).items()}


DEFAULT_SETTINGS = example_settings()
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
