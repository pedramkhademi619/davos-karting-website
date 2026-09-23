from __future__ import annotations

import ipaddress


class IpAnonymizer:
    """Data minimisation: keep an IPv4 /24 or IPv6 /48 prefix, enough for device hints."""

    @staticmethod
    def anonymize(raw: str) -> str:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            return ""
        prefix = 24 if address.version == 4 else 48
        return str(ipaddress.ip_network(f"{address}/{prefix}", strict=False))
