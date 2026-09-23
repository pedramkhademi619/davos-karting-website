from __future__ import annotations

import secrets
import string

from davos.modules.identity.application.ports.otp_code_generator import OtpCodeGenerator


class SecureOtpCodeGenerator(OtpCodeGenerator):
    def generate(self, length: int) -> str:
        return "".join(secrets.choice(string.digits) for _ in range(length))
