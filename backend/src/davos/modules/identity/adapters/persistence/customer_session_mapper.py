from __future__ import annotations

from davos.modules.identity.adapters.persistence.customer_session_model import CustomerSessionModel
from davos.modules.identity.domain.entities.customer_session import CustomerSession


class CustomerSessionMapper:
    @staticmethod
    def to_domain(model: CustomerSessionModel) -> CustomerSession:
        return CustomerSession(
            session_id=model.id,
            user_id=model.user_id,
            token_digest=model.token_digest,
            user_agent=model.user_agent,
            ip_hint=model.ip_hint,
            created_at=model.created_at,
            expires_at=model.expires_at,
            last_seen_at=model.last_seen_at,
            revoked_at=model.revoked_at,
        )

    @staticmethod
    def to_model(session: CustomerSession) -> CustomerSessionModel:
        return CustomerSessionModel(
            id=session.id,
            user_id=session.user_id,
            token_digest=session.token_digest,
            user_agent=session.user_agent,
            ip_hint=session.ip_hint,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_seen_at=session.last_seen_at,
            revoked_at=session.revoked_at,
        )
