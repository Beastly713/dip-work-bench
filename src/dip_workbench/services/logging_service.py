"""Local logging infrastructure."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LoggingService:
    """Configure and own DIP Workbench's local logging handlers."""

    def __init__(
        self,
        log_directory: Path,
        *,
        level: int = logging.INFO,
        max_bytes: int = 2_000_000,
        backup_count: int = 3,
    ) -> None:
        self._log_directory = log_directory
        self._level = level
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._logger = logging.getLogger("dip_workbench")
        self._owned_handlers: list[logging.Handler] = []

    @property
    def log_path(self) -> Path:
        """Return the configured rotating log-file path."""
        return self._log_directory / "dip-workbench.log"

    @property
    def logger(self) -> logging.Logger:
        """Return the application logger, configuring it when needed."""
        return self.configure()

    def configure(self) -> logging.Logger:
        """Configure file and console handlers exactly once."""
        if self._owned_handlers:
            return self._logger

        self._log_directory.mkdir(parents=True, exist_ok=True)
        self._logger.setLevel(self._level)
        self._logger.propagate = False
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

        file_handler = RotatingFileHandler(
            self.log_path,
            maxBytes=self._max_bytes,
            backupCount=self._backup_count,
            encoding="utf-8",
        )
        console_handler = logging.StreamHandler()
        for handler in (file_handler, console_handler):
            handler.setLevel(self._level)
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._owned_handlers.append(handler)
        return self._logger

    def close(self) -> None:
        """Remove and close only handlers owned by this service."""
        for handler in self._owned_handlers:
            self._logger.removeHandler(handler)
            handler.close()
        self._owned_handlers.clear()
