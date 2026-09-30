""".env.example is the complete configuration reference: every setting AppSettings declares is in it with a working
value, nothing in it is unused, and a missing setting stops the program by name without printing any value."""

from __future__ import annotations

import re

import pytest
from pydantic import ValidationError

from davos.platform.settings.app_settings import AppSettings
from tests.fakes.standard_config import EXAMPLE_ENV

# Read by docker-compose.yml or the web app's build, not by the backend.
NOT_BACKEND_SETTINGS = {
    "HTTP_PORT",
    "API_WORKERS",
    "FRONTEND_REPLICAS",
    "DAVOS_VERSION",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "REDIS_PASSWORD",
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "VENUE_LATITUDE",
    "VENUE_LONGITUDE",
}
_SET = re.compile(r"^([A-Z][A-Z0-9_]+)=")
_COMMENTED = re.compile(r"^#\s*([A-Z][A-Z0-9_]+)=")


def lines() -> list[str]:
    return EXAMPLE_ENV.read_text(encoding="utf-8").splitlines()


def declared() -> set[str]:
    return {name.upper() for name in AppSettings.model_fields}


def test_every_setting_is_set_in_the_example() -> None:
    written = {m.group(1) for line in lines() if (m := _SET.match(line))}
    assert not declared() - written, f"add these to .env.example: {sorted(declared() - written)}"


def test_nothing_in_the_example_is_unused_or_commented_out() -> None:
    written = {m.group(1) for line in lines() if (m := _SET.match(line))}
    assert not written - declared() - NOT_BACKEND_SETTINGS, f"nothing reads: {sorted(written - declared())}"
    commented = [m.group(1) for line in lines() if (m := _COMMENTED.match(line))]
    assert not commented, f"there are no defaults in code, so these must have a value: {commented}"


def test_the_example_alone_is_a_complete_working_configuration() -> None:
    settings = AppSettings(_env_file=EXAMPLE_ENV)  # type: ignore[call-arg]
    settings.validate_for_environment()  # development accepts the example secrets


def test_a_missing_setting_is_named_and_no_value_is_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in declared():
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError) as error:
        AppSettings(_env_file=None, otp_hmac_secret="a-real-secret-that-must-not-leak")  # type: ignore[call-arg]
    message = str(error.value)
    assert "database_url" in message and "Field required" in message
    assert "a-real-secret-that-must-not-leak" not in message
