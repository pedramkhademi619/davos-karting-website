from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from davos.modules.administration.adapters.security.scrypt_password_hasher import ScryptPasswordHasher
from davos.modules.administration.adapters.security.sha256_admin_token_service import Sha256AdminTokenService
from davos.modules.administration.domain.entities.admin_session import AdminSession
from davos.modules.administration.domain.entities.admin_user import AdminUser
from davos.modules.administration.domain.enums.admin_role import AdminRole
from davos.modules.administration.domain.errors.weak_password_error import WeakPasswordError
from davos.shared_kernel.domain.errors.validation_error import ValidationError

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
hasher = ScryptPasswordHasher()


def test_passwords_are_stored_salted_and_verified_in_constant_time() -> None:
    first, second = hasher.hash("Correct-horse-42"), hasher.hash("Correct-horse-42")
    assert first != second and first.startswith("scrypt$") and "Correct-horse-42" not in first
    assert hasher.verify("Correct-horse-42", first) and not hasher.verify("correct-horse-42", first)


@pytest.mark.parametrize("stored", ["", "bcrypt$x", "scrypt$1$2", "scrypt$16384$8$1$!!$!!", "plain-password"])
def test_malformed_hashes_simply_fail(stored: str) -> None:
    assert hasher.verify("anything", stored) is False


@pytest.mark.parametrize("password", ["short1", "onlyletterslong", "123456789012345", "x" * 201])
def test_weak_passwords_are_refused(password: str) -> None:
    with pytest.raises(WeakPasswordError):
        AdminUser.check_password_strength(password)


@pytest.mark.parametrize("username", ["ab", "1owner", "Owner Name", "o" * 33, "مدیر"])
def test_usernames_are_simple_lowercase_latin(username: str) -> None:
    with pytest.raises(ValidationError):
        AdminUser.create(username=username, display_name="", password_hash="h", role=AdminRole.STAFF, now=NOW)


def test_five_wrong_passwords_lock_the_account_for_fifteen_minutes() -> None:
    admin = AdminUser.create(username=" Owner ", display_name="", password_hash="h", role=AdminRole.OWNER, now=NOW)
    assert admin.username == "owner"
    for _ in range(4):
        admin.record_failed_login(NOW)
    assert not admin.is_locked_at(NOW)
    admin.record_failed_login(NOW)
    assert admin.is_locked_at(NOW) and admin.seconds_locked(NOW) == 900
    assert not admin.is_locked_at(NOW + timedelta(minutes=15))
    admin.record_login(NOW + timedelta(minutes=16))
    assert admin.failed_attempts == 0 and admin.locked_until is None


def test_admin_sessions_end_on_expiry_idle_time_or_revocation() -> None:
    session = AdminSession.start(
        admin_id=AdminUser.create(
            username="owner", display_name="", password_hash="h", role=AdminRole.OWNER, now=NOW
        ).id,
        token_digest="d",
        now=NOW,
        lifetime=timedelta(hours=12),
        ip_hint="1.2.3.4",
        user_agent="ua",
    )
    assert session.is_active(NOW + timedelta(hours=1))
    assert not session.is_active(NOW + timedelta(hours=2, minutes=1))  # idle for more than two hours
    session.touch(NOW + timedelta(hours=1, minutes=59))
    assert session.is_active(NOW + timedelta(hours=3))
    assert not session.is_active(NOW + timedelta(hours=12))
    session.revoke(NOW)
    assert not session.is_active(NOW)


def test_admin_tokens_are_random_and_only_digests_are_kept() -> None:
    tokens = Sha256AdminTokenService()
    a, b = tokens.new_token(), tokens.new_token()
    assert a != b and len(a) >= 40 and tokens.digest(a) != a and len(tokens.digest(a)) == 64
