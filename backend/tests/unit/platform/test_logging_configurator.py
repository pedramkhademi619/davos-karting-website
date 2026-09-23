import io
import logging
import logging.config

from uvicorn.config import LOGGING_CONFIG

from davos.platform.observability.logging_configurator import LoggingConfigurator
from davos.platform.observability.request_context import request_id_var
from tests.support.logging_state import preserved_logging_state


def _logger_with_stream() -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    logger = logging.getLogger("logging-configurator-test")
    logger.handlers = [LoggingConfigurator.build_handler(stream)]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger, stream


def test_every_line_carries_the_request_id() -> None:
    logger, stream = _logger_with_stream()
    token = request_id_var.set("req-abc-123")
    try:
        logger.info("something happened")
    finally:
        request_id_var.reset(token)
    assert "request_id=req-abc-123" in stream.getvalue()


def test_personal_data_is_masked_in_the_final_output() -> None:
    logger, stream = _logger_with_stream()
    logger.info("otp sent to %s with Authorization: Bearer abc.def-123", "09123456789")
    output = stream.getvalue()
    assert "09123456789" not in output and "abc.def-123" not in output


def _install_after_uvicorn_has_configured_its_own_logging(level: str = "INFO") -> io.StringIO:
    """Uvicorn applies its logging config first and only then imports the app, which is what calls install()."""
    logging.config.dictConfig(LOGGING_CONFIG)
    stream = io.StringIO()
    LoggingConfigurator.install(level, stream)
    return stream


def test_uvicorn_access_lines_are_masked_like_everything_else() -> None:
    with preserved_logging_state():
        stream = _install_after_uvicorn_has_configured_its_own_logging()
        logging.getLogger("uvicorn.access").info(
            '%s - "%s %s HTTP/%s" %d', "172.22.0.1:45644", "GET", "/x?mobile=09123456789&token=abcdef123456", "1.1", 200
        )
    output = stream.getvalue()
    assert "09123456789" not in output and "abcdef123456" not in output
    assert "GET /x?mobile=[mobile]" in output and "request_id=" in output


def test_uvicorn_error_lines_are_written_once_in_the_shared_format() -> None:
    with preserved_logging_state():
        stream = _install_after_uvicorn_has_configured_its_own_logging()
        logging.getLogger("uvicorn.error").warning("worker boot failed")
    assert stream.getvalue().count("worker boot failed") == 1
    assert "request_id=" in stream.getvalue()


def test_the_configured_level_also_governs_uvicorn_loggers() -> None:
    with preserved_logging_state():
        stream = _install_after_uvicorn_has_configured_its_own_logging("WARNING")
        logging.getLogger("uvicorn.access").info("GET / 200")
    assert stream.getvalue() == ""
