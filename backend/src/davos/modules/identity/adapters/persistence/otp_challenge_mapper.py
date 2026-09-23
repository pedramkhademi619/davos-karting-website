from __future__ import annotations

from davos.modules.identity.adapters.persistence.otp_challenge_model import OtpChallengeModel
from davos.modules.identity.domain.entities.otp_challenge import OtpChallenge


class OtpChallengeMapper:
    @staticmethod
    def to_domain(model: OtpChallengeModel) -> OtpChallenge:
        return OtpChallenge(
            challenge_id=model.id,
            mobile=model.mobile,
            code_digest=model.code_digest,
            created_at=model.created_at,
            expires_at=model.expires_at,
            max_attempts=model.max_attempts,
            attempts=model.attempts,
            consumed_at=model.consumed_at,
            superseded_at=model.superseded_at,
        )

    @staticmethod
    def to_model(challenge: OtpChallenge) -> OtpChallengeModel:
        return OtpChallengeModel(
            id=challenge.id,
            mobile=challenge.mobile,
            code_digest=challenge.code_digest,
            created_at=challenge.created_at,
            expires_at=challenge.expires_at,
            max_attempts=challenge.max_attempts,
            attempts=challenge.attempts,
            consumed_at=challenge.consumed_at,
            superseded_at=challenge.superseded_at,
        )
