from __future__ import annotations

from urllib.parse import urlsplit

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError

# The secret value .env.example ships with; production refuses to start with it.
_EXAMPLE_SECRET = "dev-only-insecure-secret-change-me-0123456789"  # noqa: S105 - a known-bad example, not a secret


class AppSettings(BaseSettings):
    """The backend's configuration: what each setting is, never what it is set to.

    Every value comes from the environment, normally the repository's ``.env`` (docker-compose.yml hands the containers
    that file). Nothing has a default here: a missing value stops the program at start-up with the names of the missing
    settings, instead of silently running with a value written in code. ``.env.example`` holds a complete, working set
    of development values in the same order as this class (a test keeps the two in step); it is the reference for what
    each setting means in practice. Modules never read the environment: the composition root passes them what they
    need. ``validate_for_environment`` additionally refuses to start in production with example secrets, development
    switches or http:// addresses.

    Not here on purpose: what the owner edits in the admin panel (prices, karts per session, closed days, hold time)
    and the owner's riding rules (ages, height, seats), which are business rules in the domain.
    """

    # hide_input_in_errors: a missing setting must never print the other values (secrets) into a log.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False, hide_input_in_errors=True)

    # ---- site ---------------------------------------------------------------------------------------------------
    app_env: AppEnvironment
    log_level: str
    public_base_url: str
    # Online booking on its own subdomain (the booking page, sign-in, the customer's tickets, the payment result).
    # Empty = everything on PUBLIC_BASE_URL.
    booking_base_url: str
    # Extra origins allowed to call the API from a browser; the two site addresses above are always allowed.
    cors_allowed_origins: list[str]
    # The venue's phone number (bookings by phone, questions): shown on the site and quoted by the assistant.
    contact_phone: str

    # ---- persistence and shared state ---------------------------------------------------------------------------
    database_url: str  # docker-compose.yml sets the containers' own (service host names)
    db_pool_size: int  # per API worker process (API_WORKERS processes run side by side)
    db_max_overflow: int
    db_pool_timeout_seconds: float
    redis_url: str  # docker-compose.yml sets the containers' own
    # Connections the API keeps open to outside services (AI provider, bank, SMS), shared by all of them.
    outbound_http_max_connections: int

    # ---- secrets: each has a single purpose so one leak does not compromise the others --------------------------
    otp_hmac_secret: SecretStr
    session_csrf_secret: SecretStr
    booking_webhook_secret: SecretStr
    booking_webhook_secret_previous: SecretStr  # accepted during key rotation only; empty otherwise

    # ---- development-only behaviour, must stay off in production ------------------------------------------------
    dev_sms_echo_enabled: bool

    # ---- customer sign-in (SMS one-time code) and sessions ------------------------------------------------------
    otp_code_length: int
    otp_ttl_seconds: int
    otp_max_attempts: int  # wrong codes before the code is burnt
    otp_resend_cooldown_seconds: int
    otp_requests_per_mobile_per_hour: int  # the real anti-abuse limit
    # Per-IP limits are generous: many mobile customers share one public IP (carrier-grade NAT).
    otp_requests_per_ip_per_hour: int
    otp_verifications_per_ip_per_15_minutes: int
    session_cookie_name: str
    session_lifetime_days: int
    cookie_secure: bool

    # ---- admin panel ----------------------------------------------------------------------------------------------
    admin_cookie_name: str
    admin_session_hours: int
    admin_idle_timeout_minutes: int
    admin_max_failed_logins: int  # then the account is locked for ADMIN_LOCKOUT_MINUTES
    admin_lockout_minutes: int
    admin_logins_per_ip_per_15_minutes: int
    # Creates the first owner account on start-up when there is no admin yet (ignored afterwards); empty = off.
    admin_bootstrap_username: str
    admin_bootstrap_password: SecretStr

    # ---- AI assistant: any OpenAI-compatible provider; empty address, key or model = FAQ-links-only mode ----------
    ai_base_url: str
    ai_api_key: SecretStr
    ai_model: str
    ai_timeout_seconds: float
    # Before an answer is shown, a second small request asks whether the sources it cites really say what it claims.
    ai_support_check_enabled: bool
    ai_support_check_timeout_seconds: float  # a check that takes longer is skipped and the answer is shown
    ai_token_limit_param: str  # max_tokens, or max_completion_tokens for providers and reasoning models that want it
    ai_send_temperature: bool  # some reasoning models reject a temperature
    ai_temperature: float
    ai_min_output_tokens: int  # reasoning models think inside the output limit; give them room (e.g. 2000)
    ai_max_output_tokens: int
    ai_daily_token_budget: int
    ai_max_concurrency: int
    ai_queue_wait_seconds: float  # how long a question may wait for a free slot before the fallback answer
    ai_breaker_failure_threshold: int
    ai_breaker_recovery_seconds: float
    # Optional backup model on the same provider, used only when the main model fails; empty = none.
    ai_fallback_model: str
    ai_fallback_token_limit_param: str
    ai_fallback_send_temperature: bool
    ai_fallback_min_output_tokens: int  # 0 = same as AI_MAX_OUTPUT_TOKENS
    # Owner-editable assistant content: a style-notes file and a folder of knowledge .txt files (empty = off).
    assistant_persona_file: str
    assistant_knowledge_dir: str
    assistant_max_question_chars: int
    assistant_questions_per_ip_per_hour: int
    assistant_questions_per_conversation: int
    assistant_retention_days: int  # stored interactions are purged after this
    assistant_booking_facts_cache_seconds: float  # how stale the admin settings it quotes may be
    # Short follow-up memory ("و برای پنجشنبه؟"), kept in Redis.
    conversation_context_turns: int
    conversation_context_ttl_seconds: int
    # Answer cache: a general question that means the same as one answered before is answered from the stored answer,
    # found by meaning with a small embedding model on this machine (docs/ASSISTANT_EVALUATION.md).
    semantic_cache_enabled: bool
    # Folder made by `python -m davos.tools.fetch_embedding_model` (docker-compose.yml sets the API's to the mounted
    # backend/models). Empty or missing files = the cache stays off and every question goes to the language model.
    semantic_cache_model_dir: str
    semantic_cache_similarity_threshold: float  # cosine similarity of the two questions, measured, not guessed
    # The model's check: a stored answer a little less similar than the threshold is served when the configured
    # language model confirms that one answer fits both questions (a tiny request, a second or less).
    semantic_cache_verify_with_model: bool
    semantic_cache_verify_from_similarity: float
    semantic_cache_verify_timeout_seconds: float  # a check that takes longer counts as no
    semantic_cache_candidate_limit: int  # nearest stored answers checked per question
    semantic_cache_max_text_chars: int  # a question is embedded up to this length
    semantic_cache_threads: int  # CPU threads the embedding model uses in each API process

    # ---- payments: PAYMENT_PROVIDER picks the gateway; its credentials come only from the environment ----------------
    payment_provider: str  # mellat | zarinpal
    payments_enabled: bool
    # Where the bank sends the customer back. Empty = derived from the booking site.
    payment_callback_url: str
    payment_gateway_timeout_seconds: float
    payment_attempt_ttl_minutes: int  # an unpaid attempt expires after this
    payment_hold_extension_minutes: int  # a paid hold is kept this long for the bank's final confirmation
    payment_callbacks_per_ip_per_minute: int
    payment_reconcile_after_seconds: int  # attempts stuck longer than this are checked with the bank
    payment_reconcile_batch_size: int
    mellat_terminal_id: int
    mellat_username: str
    mellat_password: SecretStr
    mellat_service_url: str
    mellat_start_pay_url: str
    zarinpal_sandbox: bool
    zarinpal_merchant_id: str
    zarinpal_api_host: str
    zarinpal_sandbox_host: str
    # Lets developers pay a clearly labelled test order against the sandbox. Never allowed in production.
    payments_sandbox_orders_enabled: bool

    # ---- SMS: "recording" sends nothing (development); "kavenegar" uses the Kavenegar API -------------------------
    sms_provider: str
    kavenegar_api_url: str
    kavenegar_api_key: SecretStr
    kavenegar_sender: str  # the dedicated line number, used for staff messages and texts without a template
    kavenegar_otp_template: str  # a verify/lookup template approved in the Kavenegar panel, e.g. davos-otp
    kavenegar_reservation_template: str
    sms_timeout_seconds: float

    # ---- integration with the counter's booking app (off until it has credentials) --------------------------------
    booking_integration_enabled: bool
    booking_webhook_tolerance_seconds: int

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
            if value == _EXAMPLE_SECRET or len(value) < 32:
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
