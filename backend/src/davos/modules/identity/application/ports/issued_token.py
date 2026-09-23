from dataclasses import dataclass


@dataclass(frozen=True)
class IssuedToken:
    raw: str
    digest: str
