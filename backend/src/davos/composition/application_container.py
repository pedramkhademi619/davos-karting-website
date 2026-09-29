from __future__ import annotations

import logging
from datetime import timedelta

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from davos.composition.adapters.reservation_order_quote_port import ReservationOrderQuotePort
from davos.composition.adapters.sandbox_order_quote_port import SandboxOrderQuotePort
from davos.composition.adapters.schedule_booking_facts import ScheduleBookingFacts
from davos.composition.adapters.sms_otp_delivery import SmsOtpDelivery
from davos.composition.policy_factory import PolicyFactory
from davos.modules.administration.adapters.persistence.sqlalchemy_admin_session_repository import (
    SqlAlchemyAdminSessionRepository,
)
from davos.modules.administration.adapters.persistence.sqlalchemy_admin_user_repository import (
    SqlAlchemyAdminUserRepository,
)
from davos.modules.administration.adapters.security.scrypt_password_hasher import ScryptPasswordHasher
from davos.modules.administration.adapters.security.sha256_admin_token_service import Sha256AdminTokenService
from davos.modules.administration.application.use_cases.admin_login_use_case import AdminLoginUseCase
from davos.modules.administration.application.use_cases.admin_logout_use_case import AdminLogoutUseCase
from davos.modules.administration.application.use_cases.authenticate_admin_use_case import AuthenticateAdminUseCase
from davos.modules.administration.application.use_cases.manage_admins_use_case import ManageAdminsUseCase
from davos.modules.assistant.adapters.ai.disabled_ai_chat import DisabledAiChat
from davos.modules.assistant.adapters.ai.fallback_ai_chat import FallbackAiChat
from davos.modules.assistant.adapters.ai.openai_compatible_chat_adapter import OpenAICompatibleChatAdapter
from davos.modules.assistant.adapters.ai.resilient_ai_chat import ResilientAiChat
from davos.modules.assistant.adapters.budget.redis_ai_budget import RedisAiBudget
from davos.modules.assistant.adapters.context.in_memory_conversation_context import InMemoryConversationContext
from davos.modules.assistant.adapters.context.redis_conversation_context import RedisConversationContext
from davos.modules.assistant.adapters.knowledge.text_file_knowledge_source import TextFileKnowledgeSource
from davos.modules.assistant.adapters.persistence.pg_trgm_knowledge_search import PgTrgmKnowledgeSearch
from davos.modules.assistant.adapters.persistence.sqlalchemy_interaction_log import SqlAlchemyInteractionLog
from davos.modules.assistant.adapters.persistence.sqlalchemy_knowledge_index import SqlAlchemyKnowledgeIndex
from davos.modules.assistant.adapters.persona.file_assistant_persona import FileAssistantPersona
from davos.modules.assistant.application.ports.ai_budget_port import AiBudgetPort
from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.assistant_persona_port import AssistantPersonaPort
from davos.modules.assistant.application.ports.conversation_context_port import ConversationContextPort
from davos.modules.assistant.application.use_cases.ask_assistant_use_case import AskAssistantUseCase
from davos.modules.assistant.application.use_cases.index_knowledge_entry_use_case import IndexKnowledgeEntryUseCase
from davos.modules.assistant.application.use_cases.purge_expired_interactions_use_case import (
    PurgeExpiredInteractionsUseCase,
)
from davos.modules.assistant.application.use_cases.submit_feedback_use_case import SubmitFeedbackUseCase
from davos.modules.assistant.application.use_cases.sync_knowledge_documents_use_case import (
    SyncKnowledgeDocumentsUseCase,
)
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.booking.adapters.persistence.sqlalchemy_booking_record_repository import (
    SqlAlchemyBookingRecordRepository,
)
from davos.modules.booking.adapters.persistence.sqlalchemy_webhook_inbox_repository import (
    SqlAlchemyWebhookInboxRepository,
)
from davos.modules.booking.application.services.booking_event_processor import BookingEventProcessor
from davos.modules.booking.application.use_cases.get_booking_return_status_use_case import (
    GetBookingReturnStatusUseCase,
)
from davos.modules.booking.application.use_cases.process_booking_webhook_use_case import (
    ProcessBookingWebhookUseCase,
)
from davos.modules.booking.application.use_cases.reprocess_failed_webhooks_use_case import (
    ReprocessFailedWebhooksUseCase,
)
from davos.modules.booking.domain.services.booking_event_parser import BookingEventParser
from davos.modules.booking.domain.services.webhook_signature_verifier import WebhookSignatureVerifier
from davos.modules.identity.adapters.persistence.sqlalchemy_otp_challenge_repository import (
    SqlAlchemyOtpChallengeRepository,
)
from davos.modules.identity.adapters.persistence.sqlalchemy_session_repository import SqlAlchemySessionRepository
from davos.modules.identity.adapters.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
from davos.modules.identity.adapters.security.csrf_token_service import CsrfTokenService
from davos.modules.identity.adapters.security.hmac_otp_hasher import HmacOtpHasher
from davos.modules.identity.adapters.security.secure_otp_code_generator import SecureOtpCodeGenerator
from davos.modules.identity.adapters.security.sha256_session_token_service import Sha256SessionTokenService
from davos.modules.identity.application.use_cases.authenticate_session_use_case import AuthenticateSessionUseCase
from davos.modules.identity.application.use_cases.customer_directory_use_case import CustomerDirectoryUseCase
from davos.modules.identity.application.use_cases.customer_profile_use_case import CustomerProfileUseCase
from davos.modules.identity.application.use_cases.list_sessions_use_case import ListSessionsUseCase
from davos.modules.identity.application.use_cases.request_otp_use_case import RequestOtpUseCase
from davos.modules.identity.application.use_cases.revoke_session_use_case import RevokeSessionUseCase
from davos.modules.identity.application.use_cases.verify_otp_use_case import VerifyOtpUseCase
from davos.modules.identity.domain.errors.invalid_mobile_number_error import InvalidMobileNumberError
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.modules.loyalty.adapters.persistence.sqlalchemy_points_ledger_repository import (
    SqlAlchemyPointsLedgerRepository,
)
from davos.modules.loyalty.application.use_cases.award_points_use_case import AwardPointsUseCase
from davos.modules.loyalty.application.use_cases.expire_points_use_case import ExpirePointsUseCase
from davos.modules.loyalty.application.use_cases.get_loyalty_summary_use_case import GetLoyaltySummaryUseCase
from davos.modules.loyalty.application.use_cases.reverse_points_use_case import ReversePointsUseCase
from davos.modules.loyalty.application.use_cases.spend_points_use_case import SpendPointsUseCase
from davos.modules.loyalty.domain.services.tier_ladder import TierLadder
from davos.modules.loyalty.domain.value_objects.tier_rule import TierRule
from davos.modules.notifications.adapters.persistence.sqlalchemy_sms_log_repository import SqlAlchemySmsLogRepository
from davos.modules.notifications.adapters.sms.kavenegar_sms_gateway import KavenegarSmsGateway
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.use_cases.refresh_sms_statuses_use_case import RefreshSmsStatusesUseCase
from davos.modules.notifications.application.use_cases.send_bulk_sms_use_case import SendBulkSmsUseCase
from davos.modules.notifications.application.use_cases.send_transactional_sms_use_case import (
    SendTransactionalSmsUseCase,
)
from davos.modules.notifications.application.use_cases.sms_panel_use_case import SmsPanelUseCase
from davos.modules.payments.adapters.mellat.mellat_payment_gateway import MellatPaymentGateway
from davos.modules.payments.adapters.persistence.sqlalchemy_payment_repository import SqlAlchemyPaymentRepository
from davos.modules.payments.adapters.zarinpal.zarinpal_payment_gateway import ZarinpalPaymentGateway
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.services.payment_settlement_service import PaymentSettlementService
from davos.modules.payments.application.use_cases.get_payment_status_use_case import GetPaymentStatusUseCase
from davos.modules.payments.application.use_cases.handle_payment_callback_use_case import HandlePaymentCallbackUseCase
from davos.modules.payments.application.use_cases.list_payments_use_case import ListPaymentsUseCase
from davos.modules.payments.application.use_cases.reconcile_payments_use_case import ReconcilePaymentsUseCase
from davos.modules.payments.application.use_cases.start_payment_use_case import StartPaymentUseCase
from davos.modules.reservations.adapters.persistence.sqlalchemy_reservation_repository import (
    SqlAlchemyReservationRepository,
)
from davos.modules.reservations.adapters.persistence.sqlalchemy_reservation_stats_reader import (
    SqlAlchemyReservationStatsReader,
)
from davos.modules.reservations.adapters.persistence.sqlalchemy_schedule_settings_repository import (
    SqlAlchemyScheduleSettingsRepository,
)
from davos.modules.reservations.adapters.security.secure_reservation_code_generator import (
    SecureReservationCodeGenerator,
)
from davos.modules.reservations.application.use_cases.accept_reservation_payment_use_case import (
    AcceptReservationPaymentUseCase,
)
from davos.modules.reservations.application.use_cases.cancel_own_hold_use_case import CancelOwnHoldUseCase
from davos.modules.reservations.application.use_cases.confirm_paid_reservation_use_case import (
    ConfirmPaidReservationUseCase,
)
from davos.modules.reservations.application.use_cases.create_staff_reservation_use_case import (
    CreateStaffReservationUseCase,
)
from davos.modules.reservations.application.use_cases.expire_holds_use_case import ExpireHoldsUseCase
from davos.modules.reservations.application.use_cases.get_booking_calendar_use_case import GetBookingCalendarUseCase
from davos.modules.reservations.application.use_cases.get_customer_reservations_use_case import (
    GetCustomerReservationsUseCase,
)
from davos.modules.reservations.application.use_cases.get_day_availability_use_case import GetDayAvailabilityUseCase
from davos.modules.reservations.application.use_cases.get_reservation_stats_use_case import GetReservationStatsUseCase
from davos.modules.reservations.application.use_cases.hold_reservation_use_case import HoldReservationUseCase
from davos.modules.reservations.application.use_cases.quote_reservation_use_case import QuoteReservationUseCase
from davos.modules.reservations.application.use_cases.schedule_settings_use_case import ScheduleSettingsUseCase
from davos.modules.reservations.application.use_cases.search_reservations_use_case import SearchReservationsUseCase
from davos.modules.reservations.application.use_cases.staff_update_reservation_use_case import (
    StaffUpdateReservationUseCase,
)
from davos.platform.clock.system_clock import SystemClock
from davos.platform.persistence.engine_factory import create_engine, create_session_factory
from davos.platform.persistence.event_serializer import EventSerializer
from davos.platform.persistence.outbox_recorder import OutboxRecorder
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from davos.platform.rate_limiting.redis_rate_limiter import RedisRateLimiter
from davos.platform.resilience.circuit_breaker import CircuitBreaker
from davos.platform.settings.app_settings import AppSettings
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ApplicationContainer:
    """Composition root: the only place where ports are bound to concrete adapters.

    Long-lived infrastructure (engine, Redis, clock) is created once. Use cases are built per
    call so every request gets its own Unit of Work and therefore its own transaction.
    """

    def __init__(
        self,
        *,
        settings: AppSettings,
        engine: AsyncEngine,
        redis: Redis | None,
        clock: Clock,
        rate_limiter: RateLimiter,
        sms_gateway: SmsGatewayPort,
        ai_chat: AIChatPort,
        ai_budget: AiBudgetPort,
        payment_gateway: PaymentGatewayPort,
        order_quotes: OrderQuotePort | None = None,
        http_client: httpx.AsyncClient | None = None,
        assistant_persona: AssistantPersonaPort | None = None,
        conversation_context: ConversationContextPort | None = None,
    ) -> None:
        self.settings = settings
        self.engine = engine
        self.redis = redis
        self.clock = clock
        self.rate_limiter = rate_limiter
        self.sms_gateway = sms_gateway
        self.ai_chat = ai_chat
        self.ai_budget = ai_budget
        self.payment_gateway = payment_gateway
        self.order_quotes: OrderQuotePort = order_quotes or ReservationOrderQuotePort(
            self.quote_reservation, self.accept_reservation_payment
        )
        self._http_client = http_client
        self._assistant_persona = assistant_persona or FileAssistantPersona(settings.assistant_persona_file)
        self._booking_facts = ScheduleBookingFacts(
            self.schedule_settings,
            contact_phone=settings.contact_phone,
            cache_seconds=settings.assistant_booking_facts_cache_seconds,
        )
        self._normalizer = PersianTextNormalizer()
        self._assistant_policy = PolicyFactory.assistant(settings)
        self.session_factory: async_sessionmaker[AsyncSession] = create_session_factory(engine)
        self._conversation_context: ConversationContextPort = conversation_context or (
            RedisConversationContext(
                redis,
                max_turns=settings.conversation_context_turns,
                ttl_seconds=settings.conversation_context_ttl_seconds,
            )
            if redis is not None
            else InMemoryConversationContext(
                clock,
                max_turns=settings.conversation_context_turns,
                ttl_seconds=settings.conversation_context_ttl_seconds,
            )
        )
        self._outbox = OutboxRecorder(serializer=EventSerializer(), clock=clock)
        self._otp_hasher = HmacOtpHasher(settings.otp_hmac_secret.get_secret_value())
        self._tokens = Sha256SessionTokenService()
        self.csrf = CsrfTokenService(settings.session_csrf_secret.get_secret_value())
        self._otp_policy = PolicyFactory.otp(settings)
        self._otp_limits = PolicyFactory.otp_limits(settings)
        self._admin_security = PolicyFactory.admin_security(settings)
        self._password_hasher = ScryptPasswordHasher()
        self._admin_tokens = Sha256AdminTokenService()
        self._reservation_codes = SecureReservationCodeGenerator()
        # SAMPLE tier thresholds for development. The real names and thresholds are business decisions that
        # administrators will configure; nothing here is a statement about Davos Karting's actual programme.
        self._tier_ladder = TierLadder(
            [TierRule("Regular", 0), TierRule("Silver", 1000), TierRule("Gold", 5000), TierRule("VIP", 10000)]
        )

    @classmethod
    def build(cls, settings: AppSettings) -> ApplicationContainer:
        settings.validate_for_environment()
        clock = SystemClock()
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        pool = settings.outbound_http_max_connections
        http_client = httpx.AsyncClient(limits=httpx.Limits(max_connections=pool, max_keepalive_connections=pool // 2))
        return cls(
            settings=settings,
            engine=create_engine(settings),
            redis=redis,
            clock=clock,
            rate_limiter=RedisRateLimiter(redis, clock),
            sms_gateway=cls._build_sms_gateway(settings, http_client),
            ai_chat=cls._build_ai_chat(settings, http_client),
            ai_budget=RedisAiBudget(redis, daily_limit=settings.ai_daily_token_budget, clock=clock),
            payment_gateway=cls._build_payment_gateway(settings, http_client),
            order_quotes=SandboxOrderQuotePort() if settings.payments_sandbox_orders_enabled else None,
            http_client=http_client,
        )

    def dev_otp_code(self, raw_mobile: str) -> str | None:
        """The code just sent to this number, for local development only.

        Only with DEV_SMS_ECHO_ENABLED (the API refuses to start in production with it) and the recording SMS gateway,
        which sends nothing: the sign-in form can then show the code instead of making developers read the log.
        """
        if not self.settings.dev_sms_echo_enabled or self.settings.is_production:
            return None
        if not isinstance(self.sms_gateway, RecordingSmsGateway):
            return None
        try:
            mobile = MobileNumber.parse(raw_mobile).local
        except InvalidMobileNumberError:
            return None
        for message in reversed(self.sms_gateway.sent):
            if message.to_local_mobile == mobile and message.template_key == SmsOtpDelivery.TEMPLATE_KEY:
                return message.parameters.get("code")
        return None

    @staticmethod
    def _build_sms_gateway(settings: AppSettings, http_client: httpx.AsyncClient) -> SmsGatewayPort:
        if settings.sms_provider == "kavenegar" and settings.kavenegar_api_key.get_secret_value():
            return KavenegarSmsGateway(
                http_client=http_client,
                api_key=settings.kavenegar_api_key.get_secret_value(),
                sender=settings.kavenegar_sender,
                templates={
                    "otp": settings.kavenegar_otp_template,
                    "reservation_confirmed": settings.kavenegar_reservation_template,
                },
                base_url=settings.kavenegar_api_url,
                timeout_seconds=settings.sms_timeout_seconds,
            )
        if settings.sms_provider == "kavenegar":
            logger.warning("SMS_PROVIDER is kavenegar but KAVENEGAR_API_KEY is empty; no SMS will be sent")
        return RecordingSmsGateway(echo=settings.dev_sms_echo_enabled)

    @staticmethod
    def _build_payment_gateway(settings: AppSettings, http_client: httpx.AsyncClient) -> PaymentGatewayPort:
        if settings.payment_provider == "zarinpal":
            return ZarinpalPaymentGateway(
                http_client=http_client,
                merchant_id=settings.zarinpal_merchant_id,
                sandbox=settings.zarinpal_sandbox,
                api_host=settings.zarinpal_api_host,
                sandbox_host=settings.zarinpal_sandbox_host,
                timeout_seconds=settings.payment_gateway_timeout_seconds,
            )
        return MellatPaymentGateway(
            http_client=http_client,
            terminal_id=settings.mellat_terminal_id,
            username=settings.mellat_username,
            password=settings.mellat_password.get_secret_value(),
            service_url=settings.mellat_service_url,
            start_pay_url=settings.mellat_start_pay_url,
            timeout_seconds=settings.payment_gateway_timeout_seconds,
        )

    @staticmethod
    def _build_ai_chat(settings: AppSettings, http_client: httpx.AsyncClient) -> AIChatPort:
        def model(name: str, token_limit_param: str, send_temperature: bool, min_output_tokens: int) -> AIChatPort:
            adapter = OpenAICompatibleChatAdapter(
                base_url=settings.ai_base_url,
                api_key=settings.ai_api_key.get_secret_value(),
                model=name,
                http_client=http_client,
                timeout_seconds=settings.ai_timeout_seconds,
                token_limit_param=token_limit_param,
                send_temperature=send_temperature,
                min_output_tokens=min_output_tokens,
            )
            if not adapter.is_configured:
                return DisabledAiChat()
            return ResilientAiChat(
                adapter,
                breaker=CircuitBreaker(
                    failure_threshold=settings.ai_breaker_failure_threshold,
                    recovery_seconds=settings.ai_breaker_recovery_seconds,
                    is_failure=ResilientAiChat.counts_as_failure,
                ),
                max_concurrency=settings.ai_max_concurrency,
                acquire_timeout_seconds=settings.ai_queue_wait_seconds,
            )

        primary = model(
            settings.ai_model,
            settings.ai_token_limit_param,
            settings.ai_send_temperature,
            settings.ai_min_output_tokens,
        )
        if not settings.ai_fallback_model or isinstance(primary, DisabledAiChat):
            return primary
        backup = model(
            settings.ai_fallback_model,
            settings.ai_fallback_token_limit_param,
            settings.ai_fallback_send_temperature,
            settings.ai_fallback_min_output_tokens,
        )
        return FallbackAiChat(primary, backup)

    async def aclose(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
        if self.redis is not None:
            await self.redis.aclose()
        await self.engine.dispose()

    def new_unit_of_work(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory, self._outbox)

    # ---- identity -------------------------------------------------------------------------
    def request_otp(self) -> RequestOtpUseCase:
        uow = self.new_unit_of_work()
        return RequestOtpUseCase(
            uow=uow,
            challenges=SqlAlchemyOtpChallengeRepository(uow),
            hasher=self._otp_hasher,
            code_generator=SecureOtpCodeGenerator(),
            delivery=SmsOtpDelivery(self.sms_gateway),
            rate_limiter=self.rate_limiter,
            clock=self.clock,
            policy=self._otp_policy,
            limits=self._otp_limits,
        )

    def verify_otp(self) -> VerifyOtpUseCase:
        uow = self.new_unit_of_work()
        return VerifyOtpUseCase(
            uow=uow,
            challenges=SqlAlchemyOtpChallengeRepository(uow),
            users=SqlAlchemyUserRepository(uow),
            sessions=SqlAlchemySessionRepository(uow),
            hasher=self._otp_hasher,
            tokens=self._tokens,
            rate_limiter=self.rate_limiter,
            clock=self.clock,
            limits=self._otp_limits,
            session_lifetime=timedelta(days=self.settings.session_lifetime_days),
        )

    def authenticate_session(self) -> AuthenticateSessionUseCase:
        uow = self.new_unit_of_work()
        return AuthenticateSessionUseCase(
            uow=uow,
            sessions=SqlAlchemySessionRepository(uow),
            users=SqlAlchemyUserRepository(uow),
            tokens=self._tokens,
            clock=self.clock,
        )

    def list_sessions(self) -> ListSessionsUseCase:
        uow = self.new_unit_of_work()
        return ListSessionsUseCase(uow=uow, sessions=SqlAlchemySessionRepository(uow), clock=self.clock)

    def revoke_session(self) -> RevokeSessionUseCase:
        uow = self.new_unit_of_work()
        return RevokeSessionUseCase(uow=uow, sessions=SqlAlchemySessionRepository(uow), clock=self.clock)

    # ---- assistant ------------------------------------------------------------------------
    def ask_assistant(self) -> AskAssistantUseCase:
        return AskAssistantUseCase(
            search=PgTrgmKnowledgeSearch(self.session_factory),
            chat=self.ai_chat,
            budget=self.ai_budget,
            interactions=SqlAlchemyInteractionLog(self.session_factory),
            rate_limiter=self.rate_limiter,
            clock=self.clock,
            policy=self._assistant_policy,
            persona=self._assistant_persona,
            context=self._conversation_context,
            normalizer=self._normalizer,
            booking_facts=self._booking_facts,
        )

    def submit_assistant_feedback(self) -> SubmitFeedbackUseCase:
        return SubmitFeedbackUseCase(interactions=SqlAlchemyInteractionLog(self.session_factory))

    def index_knowledge_entry(self) -> IndexKnowledgeEntryUseCase:
        return IndexKnowledgeEntryUseCase(
            index=SqlAlchemyKnowledgeIndex(self.session_factory, self._normalizer), clock=self.clock
        )

    def sync_knowledge_documents(self) -> SyncKnowledgeDocumentsUseCase | None:
        """Publishes the owner's knowledge .txt files; None when no folder is configured."""
        if not self.settings.assistant_knowledge_dir:
            return None
        return SyncKnowledgeDocumentsUseCase(
            index=SqlAlchemyKnowledgeIndex(self.session_factory, self._normalizer),
            source=TextFileKnowledgeSource(self.settings.assistant_knowledge_dir),
            clock=self.clock,
        )

    def purge_expired_interactions(self) -> PurgeExpiredInteractionsUseCase:
        return PurgeExpiredInteractionsUseCase(
            interactions=SqlAlchemyInteractionLog(self.session_factory), clock=self.clock
        )

    def knowledge_search(self) -> PgTrgmKnowledgeSearch:
        return PgTrgmKnowledgeSearch(self.session_factory)

    # ---- payments -------------------------------------------------------------------------
    def _payment_settlement(self, uow: SqlAlchemyUnitOfWork) -> PaymentSettlementService:
        return PaymentSettlementService(
            uow=uow,
            payments=SqlAlchemyPaymentRepository(uow),
            gateway=self.payment_gateway,
            orders=self.order_quotes,
            clock=self.clock,
        )

    def start_payment(self) -> StartPaymentUseCase:
        uow = self.new_unit_of_work()
        return StartPaymentUseCase(
            enabled=self.settings.payments_enabled,
            uow=uow,
            payments=SqlAlchemyPaymentRepository(uow),
            quotes=self.order_quotes,
            gateway=self.payment_gateway,
            clock=self.clock,
            callback_url=self.settings.effective_payment_callback_url,
            attempt_ttl=timedelta(minutes=self.settings.payment_attempt_ttl_minutes),
        )

    def handle_payment_callback(self) -> HandlePaymentCallbackUseCase:
        uow = self.new_unit_of_work()
        return HandlePaymentCallbackUseCase(
            uow=uow,
            payments=SqlAlchemyPaymentRepository(uow),
            settlement=self._payment_settlement(uow),
            clock=self.clock,
        )

    def get_payment_status(self) -> GetPaymentStatusUseCase:
        uow = self.new_unit_of_work()
        return GetPaymentStatusUseCase(uow=uow, payments=SqlAlchemyPaymentRepository(uow))

    def reconcile_payments(self) -> ReconcilePaymentsUseCase:
        uow = self.new_unit_of_work()
        return ReconcilePaymentsUseCase(
            uow=uow,
            payments=SqlAlchemyPaymentRepository(uow),
            settlement=self._payment_settlement(uow),
            clock=self.clock,
            stuck_for_seconds=self.settings.payment_reconcile_after_seconds,
            batch_size=self.settings.payment_reconcile_batch_size,
        )

    def list_payments(self) -> ListPaymentsUseCase:
        uow = self.new_unit_of_work()
        return ListPaymentsUseCase(uow=uow, payments=SqlAlchemyPaymentRepository(uow))

    # ---- reservations ---------------------------------------------------------------------
    def booking_calendar(self) -> GetBookingCalendarUseCase:
        uow = self.new_unit_of_work()
        return GetBookingCalendarUseCase(uow=uow, settings=SqlAlchemyScheduleSettingsRepository(uow), clock=self.clock)

    def day_availability(self) -> GetDayAvailabilityUseCase:
        uow = self.new_unit_of_work()
        return GetDayAvailabilityUseCase(
            uow=uow,
            reservations=SqlAlchemyReservationRepository(uow),
            settings=SqlAlchemyScheduleSettingsRepository(uow),
            clock=self.clock,
        )

    def hold_reservation(self) -> HoldReservationUseCase:
        uow = self.new_unit_of_work()
        return HoldReservationUseCase(
            uow=uow,
            reservations=SqlAlchemyReservationRepository(uow),
            settings=SqlAlchemyScheduleSettingsRepository(uow),
            codes=self._reservation_codes,
            clock=self.clock,
        )

    def create_staff_reservation(self) -> CreateStaffReservationUseCase:
        uow = self.new_unit_of_work()
        return CreateStaffReservationUseCase(
            uow=uow,
            reservations=SqlAlchemyReservationRepository(uow),
            settings=SqlAlchemyScheduleSettingsRepository(uow),
            codes=self._reservation_codes,
            clock=self.clock,
        )

    def cancel_own_hold(self) -> CancelOwnHoldUseCase:
        uow = self.new_unit_of_work()
        return CancelOwnHoldUseCase(uow=uow, reservations=SqlAlchemyReservationRepository(uow), clock=self.clock)

    def staff_update_reservation(self) -> StaffUpdateReservationUseCase:
        uow = self.new_unit_of_work()
        return StaffUpdateReservationUseCase(
            uow=uow, reservations=SqlAlchemyReservationRepository(uow), clock=self.clock
        )

    def customer_reservations(self) -> GetCustomerReservationsUseCase:
        uow = self.new_unit_of_work()
        return GetCustomerReservationsUseCase(uow=uow, reservations=SqlAlchemyReservationRepository(uow))

    def quote_reservation(self) -> QuoteReservationUseCase:
        uow = self.new_unit_of_work()
        return QuoteReservationUseCase(uow=uow, reservations=SqlAlchemyReservationRepository(uow), clock=self.clock)

    def accept_reservation_payment(self) -> AcceptReservationPaymentUseCase:
        uow = self.new_unit_of_work()
        return AcceptReservationPaymentUseCase(
            uow=uow,
            reservations=SqlAlchemyReservationRepository(uow),
            settings=SqlAlchemyScheduleSettingsRepository(uow),
            clock=self.clock,
            hold_extension_minutes=self.settings.payment_hold_extension_minutes,
        )

    def confirm_paid_reservation(self) -> ConfirmPaidReservationUseCase:
        uow = self.new_unit_of_work()
        return ConfirmPaidReservationUseCase(
            uow=uow,
            reservations=SqlAlchemyReservationRepository(uow),
            settings=SqlAlchemyScheduleSettingsRepository(uow),
            clock=self.clock,
        )

    def expire_reservation_holds(self) -> ExpireHoldsUseCase:
        uow = self.new_unit_of_work()
        return ExpireHoldsUseCase(uow=uow, reservations=SqlAlchemyReservationRepository(uow), clock=self.clock)

    def search_reservations(self) -> SearchReservationsUseCase:
        uow = self.new_unit_of_work()
        return SearchReservationsUseCase(uow=uow, reservations=SqlAlchemyReservationRepository(uow))

    def schedule_settings(self) -> ScheduleSettingsUseCase:
        uow = self.new_unit_of_work()
        return ScheduleSettingsUseCase(uow=uow, settings=SqlAlchemyScheduleSettingsRepository(uow), clock=self.clock)

    def reservation_stats(self) -> GetReservationStatsUseCase:
        uow = self.new_unit_of_work()
        return GetReservationStatsUseCase(uow=uow, stats=SqlAlchemyReservationStatsReader(uow))

    # ---- customers ------------------------------------------------------------------------
    def customer_profile(self) -> CustomerProfileUseCase:
        uow = self.new_unit_of_work()
        return CustomerProfileUseCase(uow=uow, users=SqlAlchemyUserRepository(uow))

    def customer_directory(self) -> CustomerDirectoryUseCase:
        uow = self.new_unit_of_work()
        return CustomerDirectoryUseCase(uow=uow, users=SqlAlchemyUserRepository(uow))

    # ---- SMS ------------------------------------------------------------------------------
    def send_bulk_sms(self) -> SendBulkSmsUseCase:
        uow = self.new_unit_of_work()
        return SendBulkSmsUseCase(
            uow=uow, gateway=self.sms_gateway, log=SqlAlchemySmsLogRepository(uow), clock=self.clock
        )

    def send_transactional_sms(self) -> SendTransactionalSmsUseCase:
        uow = self.new_unit_of_work()
        return SendTransactionalSmsUseCase(
            uow=uow, gateway=self.sms_gateway, log=SqlAlchemySmsLogRepository(uow), clock=self.clock
        )

    def refresh_sms_statuses(self) -> RefreshSmsStatusesUseCase:
        uow = self.new_unit_of_work()
        return RefreshSmsStatusesUseCase(
            uow=uow, gateway=self.sms_gateway, log=SqlAlchemySmsLogRepository(uow), clock=self.clock
        )

    def sms_panel(self) -> SmsPanelUseCase:
        uow = self.new_unit_of_work()
        return SmsPanelUseCase(uow=uow, gateway=self.sms_gateway, log=SqlAlchemySmsLogRepository(uow))

    # ---- administration -------------------------------------------------------------------
    def admin_login(self) -> AdminLoginUseCase:
        uow = self.new_unit_of_work()
        return AdminLoginUseCase(
            uow=uow,
            admins=SqlAlchemyAdminUserRepository(uow),
            sessions=SqlAlchemyAdminSessionRepository(uow),
            hasher=self._password_hasher,
            tokens=self._admin_tokens,
            rate_limiter=self.rate_limiter,
            clock=self.clock,
            session_lifetime=timedelta(hours=self.settings.admin_session_hours),
            security=self._admin_security,
        )

    def authenticate_admin(self) -> AuthenticateAdminUseCase:
        uow = self.new_unit_of_work()
        return AuthenticateAdminUseCase(
            uow=uow,
            admins=SqlAlchemyAdminUserRepository(uow),
            sessions=SqlAlchemyAdminSessionRepository(uow),
            tokens=self._admin_tokens,
            clock=self.clock,
            security=self._admin_security,
        )

    def admin_logout(self) -> AdminLogoutUseCase:
        uow = self.new_unit_of_work()
        return AdminLogoutUseCase(
            uow=uow, sessions=SqlAlchemyAdminSessionRepository(uow), tokens=self._admin_tokens, clock=self.clock
        )

    def manage_admins(self) -> ManageAdminsUseCase:
        uow = self.new_unit_of_work()
        return ManageAdminsUseCase(
            uow=uow,
            admins=SqlAlchemyAdminUserRepository(uow),
            sessions=SqlAlchemyAdminSessionRepository(uow),
            hasher=self._password_hasher,
            clock=self.clock,
        )

    # ---- loyalty --------------------------------------------------------------------------
    def award_points(self) -> AwardPointsUseCase:
        uow = self.new_unit_of_work()
        return AwardPointsUseCase(uow=uow, ledger=SqlAlchemyPointsLedgerRepository(uow, self.clock), clock=self.clock)

    def spend_points(self) -> SpendPointsUseCase:
        uow = self.new_unit_of_work()
        return SpendPointsUseCase(uow=uow, ledger=SqlAlchemyPointsLedgerRepository(uow, self.clock), clock=self.clock)

    def reverse_points(self) -> ReversePointsUseCase:
        uow = self.new_unit_of_work()
        return ReversePointsUseCase(uow=uow, ledger=SqlAlchemyPointsLedgerRepository(uow, self.clock), clock=self.clock)

    def expire_points(self) -> ExpirePointsUseCase:
        uow = self.new_unit_of_work()
        return ExpirePointsUseCase(uow=uow, ledger=SqlAlchemyPointsLedgerRepository(uow, self.clock), clock=self.clock)

    def loyalty_summary(self) -> GetLoyaltySummaryUseCase:
        uow = self.new_unit_of_work()
        return GetLoyaltySummaryUseCase(
            uow=uow,
            ledger=SqlAlchemyPointsLedgerRepository(uow, self.clock),
            ladder=self._tier_ladder,
            clock=self.clock,
        )

    # ---- booking integration --------------------------------------------------------------
    def _booking_processor(self, uow: SqlAlchemyUnitOfWork) -> BookingEventProcessor:
        return BookingEventProcessor(
            uow=uow,
            inbox=SqlAlchemyWebhookInboxRepository(uow),
            records=SqlAlchemyBookingRecordRepository(uow),
            clock=self.clock,
        )

    def process_booking_webhook(self) -> ProcessBookingWebhookUseCase:
        settings = self.settings
        return ProcessBookingWebhookUseCase(
            enabled=settings.booking_integration_enabled,
            verifier=WebhookSignatureVerifier(
                secrets=[
                    settings.booking_webhook_secret.get_secret_value(),
                    settings.booking_webhook_secret_previous.get_secret_value(),
                ],
                tolerance_seconds=settings.booking_webhook_tolerance_seconds,
            ),
            parser=BookingEventParser(),
            processor=self._booking_processor(self.new_unit_of_work()),
            clock=self.clock,
        )

    def reprocess_failed_booking_webhooks(self) -> ReprocessFailedWebhooksUseCase:
        uow = self.new_unit_of_work()
        return ReprocessFailedWebhooksUseCase(
            uow=uow,
            inbox=SqlAlchemyWebhookInboxRepository(uow),
            parser=BookingEventParser(),
            processor=self._booking_processor(uow),
        )

    def booking_return_status(self) -> GetBookingReturnStatusUseCase:
        uow = self.new_unit_of_work()
        return GetBookingReturnStatusUseCase(
            enabled=self.settings.booking_integration_enabled, uow=uow, records=SqlAlchemyBookingRecordRepository(uow)
        )
