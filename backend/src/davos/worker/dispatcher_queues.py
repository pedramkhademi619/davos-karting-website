class DispatcherQueues:
    """Queue names. SMS, AI, exports and critical events are isolated so one backlog never starves another."""

    CRITICAL = "critical"
    SMS = "sms"
    AI = "ai"
    EXPORT = "export"
    ALL = (CRITICAL, SMS, AI, EXPORT)
