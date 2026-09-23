from davos.modules.identity.application.ports.otp_code_generator import OtpCodeGenerator


class SequenceOtpCodeGenerator(OtpCodeGenerator):
    """Deterministic codes for tests: 123456, 234567, ..."""

    def __init__(self) -> None:
        self._n = 0

    def generate(self, length: int) -> str:
        self._n += 1
        return str(123456 * self._n)[:length].zfill(length)
