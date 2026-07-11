"""Tests for application infrastructure composition."""

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QSettings
from PySide6.QtWidgets import QApplication

from dip_workbench import application
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.services import (
    ImageIOService,
    ImageTransformService,
    LoggingService,
    SettingsService,
    TemporaryDirectoryManager,
)
from dip_workbench.state import DocumentStore


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
        assert isinstance(context.image_transforms, ImageTransformService)
        assert isinstance(context.document_store, DocumentStore)
        assert isinstance(context.operation_execution, OperationExecutionManager)
        assert (session / "history").is_dir()
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


def test_context_close_removes_history_and_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    context = application.build_application_context(
        log_directory=tmp_path / "logs",
        temporary_base_directory=tmp_path / "sessions",
        settings=QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat),
    )
    session = context.temporary_directories.session_directory
    source = ImageAsset(
        name="source", data=np.zeros((2, 2), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    context.document_store.set_primary_image(source)
    context.document_store.apply_image(source, operation_id="test", operation_name="Test operation")
    snapshot = context.document_store.history[0].snapshot_path
    assert snapshot.exists()
    context.close()
    context.close()
    assert not snapshot.exists()
    assert not session.exists()
