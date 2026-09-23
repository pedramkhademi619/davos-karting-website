from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError

_DEV_PLACEHOLDER = "dev-only-insecure-secret-change-me-0123456789"


class AppSettings(BaseSettings):
    """All runtime configuration, read from the environment (12-factor).

    Defaults are development-friendly; ``validate_for_environment`` refuses to start in
    production with placeholders, missing secrets or development-only switches enabled.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    public_base_url: str = "http://localhost"
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Persistence and shared state
    database_url: str = "postgresql+asyncpg://davos:davos@localhost:5432/davos"
    db_pool_size: int = 5
    db_max_overflow: int = 5
    redis_url: str = "redis://localhost:6379/0"

    # Secrets. Each has a single purpose so one leak does not compromise the others.
    otp_hmac_secret: SecretStr = SecretStr(_DEV_PLACEHOLDER)
    session_csrf_secret: SecretStr = SecretStr(_DEV_PLACEHOLDER)
    booking_webhook_secret: SecretStr = SecretStr(_DEV_PLACEHOLDER)
    booking_webhook_secret_previous: SecretStr = SecretStr("")  # accepted during key rotation only

    # Development-only behaviour, must stay off in production.
    dev_sms_echo_enabled: bool = False

    # Session cookie
    session_cookie_name: str = "davos_session"
    session_lifetime_days: int = 30
    cookie_secure: bool = True

    # AI assistant (OpenAI-compatible provider; the model id is never hardcoded)
    ai_base_url: str = ""
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = ""
    ai_timeout_seconds: float = 12.0
    ai_token_limit_param: str = "max_tokens"  # noqa: S105  # some providers require max_completion_tokens
    ai_send_temperature: bool = True  # some reasoning models reject a temperature
    ai_max_output_tokens: int = 400
    ai_daily_token_budget: int = 400_000
    ai_max_concurrency: int = 8
    ai_breaker_failure_threshold: int = 5
    ai_breaker_recovery_seconds: float = 30.0
    # Owner-editable assistant content: a style-notes file and a folder of knowledge .txt files (blank = off).
    assistant_persona_file: str = ""
    assistant_knowledge_dir: str = ""

    # Semantic answer cache and follow-up memory. All of it runs on this machine: the embedding model is a local folder,
    # vectors live in PostgreSQL (pgvector), the conversation memory in Redis. The cache switches itself off (and the
    # assistant works exactly as before) when this is disabled or the model folder is missing.
    semantic_cache_enabled: bool = False
    semantic_cache_similarity_threshold: float = 0.94  # measured on the real model: 0.88 confuses different topics
    semantic_cache_candidates: int = 8
    semantic_cache_max_age_days: int = 30
    semantic_cache_excluded_source_types: list[str] = Field(default_factory=lambda: ["policy"])
    semantic_cache_extra_discriminators: list[str] = Field(default_factory=list)
    embedding_model_path: str = ""  # folder made by `python -m davos.tools.fetch_embedding_model`
    embedding_model_name: str = "intfloat/multilingual-e5-base"
    embedding_dimension: int = 768
    embedding_threads: int = 2
    embedding_lru_size: int = 1024
    conversation_context_turns: int = 3
    conversation_context_ttl_seconds: int = 1200

    # Payments
    payment_provider: str = "zarinpal"
    zarinpal_sandbox: bool = True
    zarinpal_merchant_id: str = ""
    zarinpal_api_host: str = "https://payment.zarinpal.com"
    zarinpal_sandbox_host: str = "https://sandbox.zarinpal.com"
    payment_callback_url: str = ""
    payments_enabled: bool = False
    # Lets developers pay a clearly labelled test order against the sandbox. Never allowed in production.
    payments_sandbox_orders_enabled: bool = False

    # Booking integration
    booking_base_url: str = "https://booking.davoskarting.ir"
    booking_integration_enabled: bool = False
    booking_webhook_tolerance_seconds: int = 300

    @property
    def is_production(self) -> bool:
        return self.app_env is AppEnvironment.PRODUCTION

    def validate_for_environment(self) -> None:
        if not self.is_production:
            return
        problems: list[str] = []
        for name in ("otp_hmac_secret", "session_csrf_secret", "booking_webhook_secret"):
            value = getattr(self, name).get_secret_value()
            if value == _DEV_PLACEHOLDER or len(value) < 32:
                problems.append(f"{name} must be set to a random value of at least 32 characters")
        if self.dev_sms_echo_enabled:
            problems.append("DEV_SMS_ECHO_ENABLED must be false in production")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true in production")
        if "*" in self.cors_allowed_origins:
            problems.append("CORS_ALLOWED_ORIGINS must list explicit origins")
        if self.ai_base_url and not self.ai_base_url.startswith("https://"):
            problems.append("AI_BASE_URL must use https in production")
        if self.payments_sandbox_orders_enabled:
            problems.append("PAYMENTS_SANDBOX_ORDERS_ENABLED must be false in production")
        if self.zarinpal_sandbox and self.payments_enabled:
            problems.append("payments cannot be enabled against the sandbox in production")
        if problems:
            raise InsecureConfigurationError("; ".join(problems))
