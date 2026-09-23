class GatewayError(Exception):
    """Base for payment gateway failures. Never carries raw provider payloads."""
