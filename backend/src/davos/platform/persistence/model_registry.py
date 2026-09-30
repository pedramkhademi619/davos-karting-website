from __future__ import annotations

import importlib

_MODEL_MODULES = (
    "davos.platform.persistence.outbox_message_model",
    "davos.modules.identity.adapters.persistence.user_model",
    "davos.modules.identity.adapters.persistence.otp_challenge_model",
    "davos.modules.identity.adapters.persistence.customer_session_model",
    "davos.modules.assistant.adapters.persistence.knowledge_entry_model",
    "davos.modules.assistant.adapters.persistence.assistant_interaction_model",
    "davos.modules.payments.adapters.persistence.payment_attempt_model",
    "davos.modules.loyalty.adapters.persistence.loyalty_account_model",
    "davos.modules.loyalty.adapters.persistence.points_ledger_entry_model",
    "davos.modules.booking.adapters.persistence.booking_record_model",
    "davos.modules.booking.adapters.persistence.booking_webhook_inbox_model",
    "davos.modules.reservations.adapters.persistence.reservation_model",
    "davos.modules.reservations.adapters.persistence.schedule_settings_model",
    "davos.modules.notifications.adapters.persistence.sms_message_model",
    "davos.modules.administration.adapters.persistence.admin_user_model",
    "davos.modules.administration.adapters.persistence.admin_session_model",
)


def register_all_models() -> None:
    """Import every ORM model so ``Base.metadata`` is complete for Alembic and tests.

    New modules add their model modules here; an architecture test guards that none is missed.
    """
    for module_name in _MODEL_MODULES:
        importlib.import_module(module_name)
