from __future__ import annotations

import logging

from davos.platform.observability.request_context import request_id_var


class RequestIdFilter(logging.Filter):
    """Stamps every log record with the correlation id of the request (or task) being served."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True
