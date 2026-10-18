from enum import StrEnum


class AdminPermission(StrEnum):
    """One thing a staff member may be allowed to open or do in the admin panel.

    To add a feature: add its key here, describe it in ``PermissionCatalog`` and protect its API routes with
    ``require_permission``; the panel's permission editor and the menu pick it up from the catalog. A ``.manage`` key is
    the "may change things" level of a section whose plain key only lets the person look.
    """

    DASHBOARD = "dashboard"
    RESERVATIONS = "reservations"
    CUSTOMERS = "customers"
    PAYMENTS = "payments"
    SMS = "sms"
    ASSISTANT = "assistant"
    ASSISTANT_MANAGE = "assistant.manage"
    SETTINGS = "settings"
    SETTINGS_MANAGE = "settings.manage"
    ACCOUNTING = "accounting"
    SYSTEM = "system"
