from __future__ import annotations

from datetime import timedelta

from davos.modules.administration.domain.value_objects.admin_security_policy import AdminSecurityPolicy
from davos.modules.assistant.domain.value_objects.answer_cache_policy import AnswerCachePolicy
from davos.modules.assistant.domain.value_objects.assistant_policy import AssistantPolicy
from davos.modules.identity.application.use_cases.otp_rate_limit_policy import OtpRateLimitPolicy
from davos.modules.identity.domain.value_objects.otp_policy import OtpPolicy
from davos.platform.settings.app_settings import AppSettings


class PolicyFactory:
    """Turns the settings into the modules' policy objects. The one place that maps AppSettings fields to policies,
    so a number lives only in AppSettings (and .env), never twice. Tests build their policies here too."""

    @staticmethod
    def otp(settings: AppSettings) -> OtpPolicy:
        return OtpPolicy(
            code_length=settings.otp_code_length,
            ttl_seconds=settings.otp_ttl_seconds,
            max_attempts=settings.otp_max_attempts,
            resend_cooldown_seconds=settings.otp_resend_cooldown_seconds,
        )

    @staticmethod
    def otp_limits(settings: AppSettings) -> OtpRateLimitPolicy:
        return OtpRateLimitPolicy(
            per_mobile_limit=settings.otp_requests_per_mobile_per_hour,
            per_ip_limit=settings.otp_requests_per_ip_per_hour,
            verify_per_ip_limit=settings.otp_verifications_per_ip_per_15_minutes,
        )

    @staticmethod
    def admin_security(settings: AppSettings) -> AdminSecurityPolicy:
        return AdminSecurityPolicy(
            max_failed_logins=settings.admin_max_failed_logins,
            lockout=timedelta(minutes=settings.admin_lockout_minutes),
            idle_timeout=timedelta(minutes=settings.admin_idle_timeout_minutes),
            logins_per_ip_per_15_minutes=settings.admin_logins_per_ip_per_15_minutes,
        )

    @staticmethod
    def answer_cache(settings: AppSettings) -> AnswerCachePolicy:
        return AnswerCachePolicy(
            similarity_threshold=settings.semantic_cache_similarity_threshold,
            verify_from_similarity=settings.semantic_cache_verify_from_similarity,
            candidate_limit=settings.semantic_cache_candidate_limit,
            max_text_chars=settings.semantic_cache_max_text_chars,
        )

    @staticmethod
    def assistant(settings: AppSettings) -> AssistantPolicy:
        return AssistantPolicy(
            max_question_chars=settings.assistant_max_question_chars,
            max_output_tokens=settings.ai_max_output_tokens,
            temperature=settings.ai_temperature,
            questions_per_ip_per_hour=settings.assistant_questions_per_ip_per_hour,
            questions_per_conversation=settings.assistant_questions_per_conversation,
            interaction_retention_days=settings.assistant_retention_days,
        )
