import re

from davos.modules.identity.adapters.security.csrf_token_service import CsrfTokenService
from davos.modules.identity.adapters.security.hmac_otp_hasher import HmacOtpHasher
from davos.modules.identity.adapters.security.secure_otp_code_generator import SecureOtpCodeGenerator
from davos.modules.identity.adapters.security.sha256_session_token_service import Sha256SessionTokenService


def test_otp_digest_is_keyed_and_bound_to_the_mobile() -> None:
    a = HmacOtpHasher("secret-a" * 5)
    b = HmacOtpHasher("secret-b" * 5)
    assert a.digest("+989123456789", "123456") == a.digest("+989123456789", "123456")
    assert a.digest("+989123456789", "123456") != b.digest("+989123456789", "123456")
    assert a.digest("+989123456789", "123456") != a.digest("+989123456780", "123456")
    assert "123456" not in a.digest("+989123456789", "123456")


def test_generated_codes_are_numeric_fixed_length_and_keep_leading_zeros() -> None:
    generator = SecureOtpCodeGenerator()
    codes = {generator.generate(6) for _ in range(300)}
    assert all(re.fullmatch(r"\d{6}", c) for c in codes)
    assert len(codes) > 250  # no obvious bias or repetition
    assert any(c.startswith("0") for c in codes)


def test_session_tokens_are_unique_and_only_the_digest_is_derivable() -> None:
    service = Sha256SessionTokenService()
    first, second = service.issue(), service.issue()
    assert first.raw != second.raw
    assert first.digest == service.digest(first.raw)
    assert first.raw not in first.digest
    assert len(first.raw) >= 43  # 256 bits, url-safe base64


def test_csrf_token_binding() -> None:
    service = CsrfTokenService("c" * 40)
    token = service.token_for("session-token")
    assert service.is_valid("session-token", token)
    assert not service.is_valid("other-session", token)
    assert not service.is_valid("session-token", "")
    assert not service.is_valid("", token)
    assert not service.is_valid("session-token", token[:-1] + ("0" if token[-1] != "0" else "1"))
