from __future__ import annotations

from urllib.parse import urlsplit

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError

_DEV_PLACEHOLDER = "dev-only-insecure-secret-change-me-0123456789"


class AppSettings(BaseSettings):
    """All runtime configuration, read from the environment (12-factor), and the only place that has defaults.

    Every value that can differ between deployments or that an operator may tune lives here, grouped by concern and
    documented in ``.env.example`` in the same order. Modules never read the environment: the composition root passes
    them what they need. Defaults are development-friendly; ``validate_for_environment`` refuses to start in production
    with placeholders, missing secrets or development-only switches enabled.

    Not here on purpose: what the owner edits in the admin panel (prices, karts per session, closed days, hold time)
    and the owner's riding rules (ages, height, seats), which are business rules in the domain.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # ---- site ---------------------------------------------------------------------------------------------------
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    log_level: str = "INFO"
    public_base_url: str = "http://localhost"
    # Online booking lives on its own subdomain (e.g. https://booking.davoskarting.ir): the booking page, sign-in, the
    # customer's tickets and the payment result. Blank = everything on PUBLIC_BASE_URL (local development).
    booking_base_url: str = ""
    # Extra origins allowed to call the API from a browser; the two site addresses above are always allowed.
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    # The venue's phone number (bookings by phone, questions). Shown on the site and quoted by the assistant.
    contact_phone: str = ""

    # ---- persistence and shared state ---------------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://davos:davos@localhost:5432/davos"
    db_pool_size: int = 5  # per API worker process (API_WORKERS processes run side by side)
    db_max_overflow: int = 5
    db_pool_timeout_seconds: float = 10.0
    redis_url: str = "redis://localhost:6379/0"
    # Connections the API keeps open to outside services (AI provider, bank, SMS), shared by all of them.
    outbound_http_max_connections: int = 20

    # ---- secrets: each has a single purpose so one leak does not compromise the others --------------------------
    otp_hmac_secret: SecretStr = SecretStr(_DEV_PLACEHOLDER)
    session_csrf_secret: SecretStr = SecretStr(_DEV_PLACEHOLDER)
    booking_webhook_secret: SecretStr = SecretStr(_DEV_PLACEHOLDER)
    booking_webhook_secret_previous: SecretStr = SecretStr("")  # accepted during key rotation only

    # ---- development-only behaviour, must stay off in production ------------------------------------------------
    dev_sms_echo_enabled: bool = False

    # ---- customer sign-in (SMS one-time code) and sessions ------------------------------------------------------
    otp_code_length: int = 6
    otp_ttl_seconds: int = 120
    otp_max_attempts: int = 3  # wrong codes before the code is burnt
    otp_resend_cooldown_seconds: int = 60
    otp_requests_per_mobile_per_hour: int = 5  # the real anti-abuse limit
    # Per-IP limits are generous: many mobile customers share one public IP (carrier-grade NAT).
    otp_requests_per_ip_per_hour: int = 200
    otp_verifications_per_ip_per_15_minutes: int = 300
    session_cookie_name: str = "davos_session"
    session_lifetime_days: int = 30
    cookie_secure: bool = True

    # ---- admin panel ----------------------------------------------------------------------------------------------
    admin_cookie_name: str = "davos_admin"
    admin_session_hours: int = 12
    admin_idle_timeout_minutes: int = 120
    admin_max_failed_logins: int = 5  # then the account is locked for ADMIN_LOCKOUT_MINUTES
    admin_lockout_minutes: int = 15
    admin_logins_per_ip_per_15_minutes: int = 20
    # Creates the first owner account on start-up when there is no admin yet (ignored afterwards).
    admin_bootstrap_username: str = ""
    admin_bootstrap_password: SecretStr = SecretStr("")

    # ---- AI assistant: any OpenAI-compatible provider; the model id is never hardcoded -----------------------------
    ai_base_url: str = ""
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = ""
    ai_timeout_seconds: float = 12.0
    ai_token_limit_param: str = "max_tokens"  # noqa: S105  # some providers require max_completion_tokens
    ai_send_temperature: bool = True  # some reasoning models reject a temperature
    ai_temperature: float = 0.1  # low: answers must follow the published texts, not improvise
    ai_min_output_tokens: int = 0  # reasoning models think inside the output limit; give them room (e.g. 2000)
    ai_max_output_tokens: int = 400
    ai_daily_token_budget: int = 400_000
    ai_max_concurrency: int = 8
    ai_queue_wait_seconds: float = 0.5  # how long a question may wait for a free slot before the fallback answer
    ai_breaker_failure_threshold: int = 5
    ai_breaker_recovery_seconds: float = 30.0
    # Optional backup model on the same provider, used only when the main model fails. Reasoning models spend part of
    # the output budget on hidden thinking, so they usually need max_completion_tokens, no temperature and more tokens.
    ai_fallback_model: str = ""
    ai_fallback_token_limit_param: str = "max_tokens"  # noqa: S105
    ai_fallback_send_temperature: bool = True
    ai_fallback_min_output_tokens: int = 0  # 0 = same as ai_max_output_tokens
    # Owner-editable assistant content: a style-notes file and a folder of knowledge .txt files (blank = off).
    assistant_persona_file: str = ""
    assistant_knowledge_dir: str = ""
    assistant_max_question_chars: int = 500
    assistant_questions_per_ip_per_hour: int = 120
    assistant_questions_per_conversation: int = 20
    assistant_retention_days: int = 90  # stored interactions are purged after this
    assistant_booking_facts_cache_seconds: float = 30.0  # how stale the admin settings it quotes may be
    # Short follow-up memory ("و برای پنجشنبه؟"), kept in Redis.
    conversation_context_turns: int = 3
    conversation_context_ttl_seconds: int = 1200

    # ---- payments: PAYMENT_PROVIDER picks the gateway; its credentials come only from the environment ----------------
    payment_provider: str = "mellat"  # mellat | zarinpal
    payments_enabled: bool = False
    # Where the bank sends the customer back. Blank = derived from the booking site.
    payment_callback_url: str = ""
    payment_gateway_timeout_seconds: float = 20.0
    payment_attempt_ttl_minutes: int = 30  # an unpaid attempt expires after this
    payment_hold_extension_minutes: int = 10  # a paid hold is kept this long for the bank's final confirmation
    payment_callbacks_per_ip_per_minute: int = 30
    payment_reconcile_after_seconds: int = 120  # attempts stuck longer than this are checked with the bank
    payment_reconcile_batch_size: int = 50
    mellat_terminal_id: int = 0
    mellat_username: str = ""
    mellat_password: SecretStr = SecretStr("")
    mellat_service_url: str = "https://bpm.shaparak.ir/pgwchannel/services/pgw"
    mellat_start_pay_url: str = "https://bpm.shaparak.ir/pgwchannel/startpay.mellat"
    zarinpal_sandbox: bool = True
    zarinpal_merchant_id: str = ""
    zarinpal_api_host: str = "https://payment.zarinpal.com"
    zarinpal_sandbox_host: str = "https://sandbox.zarinpal.com"
    # Lets developers pay a clearly labelled test order against the sandbox. Never allowed in production.
    payments_sandbox_orders_enabled: bool = False

    # ---- SMS: "recording" sends nothing (development); "kavenegar" uses the Kavenegar API -------------------------
    sms_provider: str = "recording"
    kavenegar_api_url: str = "https://api.kavenegar.com/v1"
    kavenegar_api_key: SecretStr = SecretStr("")
    kavenegar_sender: str = ""  # the dedicated line number, used for staff messages and texts without a template
    kavenegar_otp_template: str = ""  # a verify/lookup template approved in the Kavenegar panel, e.g. davos-otp
    kavenegar_reservation_template: str = ""
    sms_timeout_seconds: float = 10.0

    # ---- integration with the counter's booking app (off until it has credentials) --------------------------------
    booking_integration_enabled: bool = False
    booking_webhook_tolerance_seconds: int = 300

    @property
    def is_production(self) -> bool:
        return self.app_env is AppEnvironment.PRODUCTION

    @property
    def trusted_origins(self) -> frozenset[str]:
        """Origins whose browser requests may change state: the site's own addresses plus CORS_ALLOWED_ORIGINS.

        The main site and the booking subdomain are always trusted, so forgetting to list one of them cannot silently
        break every sign-in, hold and payment with a 403.
        """
        own = (self._origin_of(self.public_base_url), self._origin_of(self.booking_base_url))
        return frozenset(origin for origin in (*self.cors_allowed_origins, *own) if origin)

    @staticmethod
    def _origin_of(url: str) -> str:
        parts = urlsplit(url.strip())
        return f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else ""

    @property
    def booking_site_url(self) -> str:
        """Where customers book and pay; the bank sends them back here, where their session cookie lives."""
        return (self.booking_base_url or self.public_base_url).rstrip("/")

    @property
    def effective_payment_callback_url(self) -> str:
        if self.payment_callback_url:
            return self.payment_callback_url
        return f"{self.booking_site_url}/api/v1/payments/{self.payment_provider}/callback"

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
        if self.payments_enabled:
            if self.payment_provider == "zarinpal" and self.zarinpal_sandbox:
                problems.append("payments cannot be enabled against the sandbox in production")
            if self.payment_provider == "mellat" and not (
                self.mellat_terminal_id and self.mellat_username and self.mellat_password.get_secret_value()
            ):
                problems.append("MELLAT_TERMINAL_ID, MELLAT_USERNAME and MELLAT_PASSWORD are required for payments")
            if not self.effective_payment_callback_url.startswith("https://"):
                problems.append("the payment callback URL must use https in production")
        if self.payment_provider not in {"mellat", "zarinpal"}:
            problems.append("PAYMENT_PROVIDER must be mellat or zarinpal")
        if self.sms_provider != "kavenegar" or not self.kavenegar_api_key.get_secret_value():
            problems.append("SMS_PROVIDER=kavenegar with KAVENEGAR_API_KEY is required in production")
        if not self.public_base_url.startswith("https://"):
            problems.append("PUBLIC_BASE_URL must use https in production")
        if self.booking_base_url and not self.booking_base_url.startswith("https://"):
            problems.append("BOOKING_BASE_URL must use https in production")
        if problems:
            raise InsecureConfigurationError("; ".join(problems))
