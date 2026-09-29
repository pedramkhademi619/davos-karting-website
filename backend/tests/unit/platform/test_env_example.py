""".env.example is the configuration reference: it must list every setting, and the defaults it shows must be the real
ones, so the file and AppSettings can never drift apart."""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path

from pydantic import SecretStr

from davos.platform.settings.app_settings import AppSettings

ENV_EXAMPLE = Path(__file__).resolve().parents[4] / ".env.example"
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
_LINE = re.compile(r"^(?P<comment>#\s)?(?P<name>[A-Z][A-Z0-9_]+)=(?P<value>.*)$")


def documented() -> dict[str, tuple[bool, str]]:
    """NAME -> (shown as a commented default, value)."""
    entries: dict[str, tuple[bool, str]] = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        match = _LINE.match(line)
        if match:
            entries[match["name"]] = (bool(match["comment"]), match["value"])
    return entries


def as_env(value: object) -> str:
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, list):
        return json.dumps(value)
    return str(value)


def test_every_setting_is_documented() -> None:
    missing = {name.upper() for name in AppSettings.model_fields} - documented().keys()
    assert not missing, f"add these to .env.example: {sorted(missing)}"


def test_every_documented_variable_is_used() -> None:
    known = {name.upper() for name in AppSettings.model_fields} | NOT_BACKEND_SETTINGS
    unknown = documented().keys() - known
    assert not unknown, f".env.example lists variables nothing reads: {sorted(unknown)}"


def test_the_defaults_shown_are_the_real_defaults() -> None:
    defaults = AppSettings(_env_file=None)  # type: ignore[call-arg]
    wrong = {
        name: (shown, as_env(getattr(defaults, name.lower())))
        for name, (commented, shown) in documented().items()
        if commented and name not in NOT_BACKEND_SETTINGS and shown != as_env(getattr(defaults, name.lower()))
    }
    assert not wrong, f"commented defaults in .env.example differ from AppSettings (shown, real): {wrong}"
