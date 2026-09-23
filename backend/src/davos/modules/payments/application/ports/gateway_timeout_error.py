from davos.modules.payments.application.ports.gateway_error import GatewayError


class GatewayTimeoutError(GatewayError):
    """No answer in time. For verification this means the outcome is UNKNOWN, not failed."""
