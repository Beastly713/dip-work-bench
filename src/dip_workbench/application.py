"""Headless application composition root for the C01 foundation."""

from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSettings, QStandardPaths

from dip_workbench.services import LoggingService, SettingsService, TemporaryDirectoryManager

APPLICATION_NAME = "DIP Workbench"
ORGANIZATION_NAME = "DIP Workbench"
APPLICATION_VERSION = "0.1.0"


def _set_application_metadata() -> None:
    QCoreApplication.setApplicationName(APPLICATION_NAME)
    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setApplicationVersion(APPLICATION_VERSION)


def _default_log_directory() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    root = Path(location) if location else Path.home() / ".local" / "share" / "dip-workbench"
    return root / "logs"


@dataclass
class ApplicationContext:
    """Own the infrastructure services created for one application run."""

    logging: LoggingService
    settings: SettingsService
    temporary_directories: TemporaryDirectoryManager
    _closed: bool = field(default=False, init=False, repr=False)

    def close(self) -> None:
        """Release application resources once, logging cleanup failures when possible."""
        if self._closed:
            return
        self._closed = True
        try:
            self.temporary_directories.cleanup()
        except Exception:
            self.logging.logger.exception("Failed to clean temporary session directory")
            raise
        finally:
            self.logging.close()


def build_application_context(
    *,
    log_directory: Path | None = None,
    temporary_base_directory: Path | None = None,
    settings: QSettings | None = None,
) -> ApplicationContext:
    """Build and inject the shared infrastructure services."""
    _set_application_metadata()
    logging_service = LoggingService(log_directory or _default_log_directory())
    logging_service.configure()
    logging_service.logger.info("Starting DIP Workbench infrastructure bootstrap")
    temporary_directories: TemporaryDirectoryManager | None = None
    try:
        settings_service = SettingsService(settings)
        temporary_directories = TemporaryDirectoryManager(temporary_base_directory)
        return ApplicationContext(logging_service, settings_service, temporary_directories)
    except Exception:
        if temporary_directories is not None:
            temporary_directories.cleanup()
        logging_service.close()
        raise


def main() -> int:
    """Initialize and cleanly stop the C01 infrastructure context."""
    context = build_application_context()
    try:
        context.logging.logger.info("Infrastructure initialization succeeded")
    finally:
        context.close()
    return 0
