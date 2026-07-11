"""Application composition and desktop startup."""

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSettings, QStandardPaths
from PySide6.QtWidgets import QApplication, QMessageBox

from dip_workbench.services import (
    ImageIOService,
    LoggingService,
    SettingsService,
    TemporaryDirectoryManager,
)
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui import MainWindow

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
    image_io: ImageIOService
    document_store: DocumentStore
    _closed: bool = field(default=False, init=False, repr=False)

    def close(self) -> None:
        """Release application resources once, logging cleanup failures when possible."""
        if self._closed:
            return
        self._closed = True
        failure: Exception | None = None
        try:
            self.document_store.close()
        except Exception as error:
            failure = error
            self.logging.logger.exception("Failed to close document store")
        try:
            self.temporary_directories.cleanup()
        except Exception as error:
            failure = failure or error
            self.logging.logger.exception("Failed to clean temporary session directory")
        self.logging.close()
        if failure is not None:
            raise failure


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
        image_io = ImageIOService()
        snapshot_store = HistorySnapshotStore(
            temporary_directories.create_subdirectory("history"), image_io
        )
        document_store = DocumentStore(snapshot_store)
        return ApplicationContext(
            logging_service,
            settings_service,
            temporary_directories,
            image_io,
            document_store,
        )
    except Exception:
        logging_service.logger.exception("Infrastructure context construction failed")
        if temporary_directories is not None:
            temporary_directories.cleanup()
        logging_service.close()
        raise


def create_qt_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create or reuse the process-wide Qt application."""
    _set_application_metadata()
    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        return existing
    return QApplication(list(argv) if argv is not None else sys.argv)


def _show_startup_error() -> None:
    QMessageBox.critical(
        None,
        APPLICATION_NAME,
        "DIP Workbench could not start.\n\nCheck the application log for more information.",
    )


def run_application(application: QApplication, context: ApplicationContext) -> int:
    """Construct, show, and execute the single-window application."""
    try:
        window = MainWindow(context.settings)
        window.show()
        return application.exec()
    except Exception:
        context.logging.logger.exception("DIP Workbench startup failed")
        _show_startup_error()
        return 1
    finally:
        context.close()


def main() -> int:
    """Start the desktop application and return its Qt exit status."""
    application = create_qt_application()
    try:
        context = build_application_context()
    except Exception:
        _show_startup_error()
        return 1
    return run_application(application, context)
