"""Tests for application infrastructure composition."""

import pytest
from PySide6.QtCore import QCoreApplication, QSettings
from PySide6.QtWidgets import QApplication

from dip_workbench import application
from dip_workbench.services import (
    ImageIOService,
    LoggingService,
    SettingsService,
    TemporaryDirectoryManager,
)


def test_build_context_uses_injected_resources(tmp_path) -> None:  # type: ignore[no-untyped-def]
    existing_application = QApplication.instance()
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
        assert isinstance(context.image_io, ImageIOService)
        assert context.logging.log_path.parent == log_directory
        assert session.parent == temporary_base
        assert context.settings.backend is backend
        assert QCoreApplication.applicationName() == application.APPLICATION_NAME
        assert QCoreApplication.organizationName() == application.ORGANIZATION_NAME
        assert QCoreApplication.applicationVersion() == application.APPLICATION_VERSION
        assert QApplication.instance() is existing_application
    finally:
        context.close()
    assert not session.exists()
    context.close()


def test_context_closes_resources_after_cleanup_failure(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    context = application.build_application_context(
        log_directory=tmp_path / "logs",
        temporary_base_directory=tmp_path / "sessions",
        settings=backend,
    )
    monkeypatch.setattr(
        context.temporary_directories,
        "cleanup",
        lambda: (_ for _ in ()).throw(RuntimeError("cleanup failed")),
    )
    try:
        with pytest.raises(RuntimeError, match="cleanup failed"):
            context.close()
    finally:
        context.logging.close()
