from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

_FRAMEWORK_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


@contextmanager
def preserved_logging_state() -> Iterator[None]:
    """Undo whatever a test does to the root and uvicorn loggers (handlers, propagation, level)."""
    root = logging.getLogger()
    saved_root = (root.handlers[:], root.level)
    saved = [(lg, lg.handlers[:], lg.propagate, lg.level) for lg in map(logging.getLogger, _FRAMEWORK_LOGGERS)]
    try:
        yield
    finally:
        root.handlers[:] = saved_root[0]
        root.setLevel(saved_root[1])
        for logger, handlers, propagate, level in saved:
            logger.handlers[:] = handlers
            logger.propagate = propagate
            logger.setLevel(level)
