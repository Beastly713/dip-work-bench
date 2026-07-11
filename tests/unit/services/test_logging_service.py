"""Tests for local rotating logging."""

import logging
from logging.handlers import RotatingFileHandler

from dip_workbench.services import LoggingService


def test_configure_creates_handlers_and_utf8_log(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = LoggingService(tmp_path / "logs", max_bytes=1234, backup_count=2)
    try:
        logger = service.configure()
        logger.info("hello café")
        for handler in logger.handlers:
            handler.flush()

        rotating = [
            handler
            for handler in logger.handlers
            if isinstance(handler, RotatingFileHandler) and handler in service._owned_handlers
        ]
        consoles = [
            handler
            for handler in logger.handlers
            if type(handler) is logging.StreamHandler and handler in service._owned_handlers
        ]
        assert service.log_path.read_text(encoding="utf-8").find("hello café") >= 0
        assert logger.propagate is False
        assert len(rotating) == 1
        assert len(consoles) == 1
        assert rotating[0].maxBytes == 1234
        assert rotating[0].backupCount == 2
    finally:
        service.close()


def test_configure_and_close_are_idempotent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = LoggingService(tmp_path)
    logger = service.configure()
    owned = tuple(service._owned_handlers)
    assert service.configure() is logger
    assert tuple(service._owned_handlers) == owned
    service.close()
    service.close()
    assert not any(handler in logger.handlers for handler in owned)
