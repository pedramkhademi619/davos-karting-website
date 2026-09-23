from __future__ import annotations

import logging
from typing import TextIO

from davos.platform.observability.request_id_filter import RequestIdFilter
from davos.platform.observability.sensitive_data_filter import SensitiveDataFilter

_FORMAT = "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


class LoggingConfigurator:
    """One handler for the whole process: correlation ids added, phone numbers/tokens/secrets masked."""

    @staticmethod
    def build_handler(stream: TextIO | None = None) -> logging.Handler:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(_FORMAT))
        handler.addFilter(RequestIdFilter())
        handler.addFilter(SensitiveDataFilter())
        return handler

    @staticmethod
    def install(level: str = "INFO", stream: TextIO | None = None) -> None:
        root = logging.getLogger()
        root.handlers = [LoggingConfigurator.build_handler(stream)]
        root.setLevel(level.upper())
        # Uvicorn keeps its own non-propagating handlers, and its access log carries URLs and query strings.
        for name in _UVICORN_LOGGERS:
            framework_logger = logging.getLogger(name)
            framework_logger.handlers = []
            framework_logger.propagate = True
            framework_logger.setLevel(level.upper())
