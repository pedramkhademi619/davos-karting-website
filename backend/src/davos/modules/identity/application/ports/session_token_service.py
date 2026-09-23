from abc import ABC, abstractmethod

from davos.modules.identity.application.ports.issued_token import IssuedToken


class SessionTokenService(ABC):
    @abstractmethod
    def issue(self) -> IssuedToken: ...

    @abstractmethod
    def digest(self, raw: str) -> str: ...
