"""Tests for the headless application composition root."""

from PySide6.QtCore import QCoreApplication, QSettings
from PySide6.QtWidgets import QApplication

from dip_workbench import application
from dip_workbench.services import LoggingService, SettingsService, TemporaryDirectoryManager


def test_build_context_uses_injected_resources(tmp_path) -> None:  # type: ignore[no-untyped-def]
    log_directory = tmp_path / "logs"
    temporary_base = tmp_path / "sessions"
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    context = application.build_application_context(
        log_directory=log_directory,
        temporary_base_directory=temporary_base,
        settings=backend,
    )
    session = context.temporary_directories.session_directory
    try:
        assert isinstance(context.logging, LoggingService)
        assert isinstance(context.settings, SettingsService)
        assert isinstance(context.temporary_directories, TemporaryDirectoryManager)
        assert context.logging.log_path.parent == log_directory
        assert session.parent == temporary_base
        assert context.settings.backend is backend
        assert QCoreApplication.applicationName() == application.APPLICATION_NAME
        assert QCoreApplication.organizationName() == application.ORGANIZATION_NAME
        assert QCoreApplication.applicationVersion() == application.APPLICATION_VERSION
        assert QApplication.instance() is None
    finally:
        context.close()
    assert not session.exists()
    context.close()


class FakeContext:
    def __init__(self) -> None:
        self.logging = FakeLogging()
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeLogging:
    @property
    def logger(self) -> "FakeLogging":
        return self

    def info(self, message: str) -> None:
        assert message


def test_main_returns_zero_and_closes_context(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    context = FakeContext()
    monkeypatch.setattr(application, "build_application_context", lambda: context)
    assert application.main() == 0
    assert context.closed
