from davos.modules.payments.application.ports.gateway_error import GatewayError


class GatewayRejectedError(GatewayError):
    def __init__(self, provider_code: int | None) -> None:
        super().__init__(f"payment gateway rejected the request (code {provider_code})")
        self.provider_code = provider_code
