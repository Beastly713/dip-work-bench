"""Tests for controlled Qt startup."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from dip_workbench import application


class FakeLogger:
    def exception(self, message: str) -> None:
        assert message


class FakeLogging:
    logger = FakeLogger()


class FakeContext:
    def __init__(self) -> None:
        self.logging = FakeLogging()
        self.settings = object()
        self.image_io = object()
        self.export_service = object()
        self.image_transforms = object()
        self.document_store = object()
        self.operation_execution = object()
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeWindow:
    shown = False

    def __init__(
        self, settings: object, controller: object, execution: object, export_service: object
    ) -> None:
        assert settings is not None
        assert controller is not None
        assert execution is not None
        assert export_service is not None

    def show(self) -> None:
        type(self).shown = True


def test_qt_application_creation_and_metadata(qapp) -> None:  # type: ignore[no-untyped-def]
    created = application.create_qt_application([])
    assert created is qapp
    assert created.applicationName() == application.APPLICATION_NAME
    assert created.organizationName() == application.ORGANIZATION_NAME
    assert created.applicationVersion() == application.APPLICATION_VERSION


def test_runner_shows_window_returns_exit_code_and_closes(monkeypatch, qapp) -> None:  # type: ignore[no-untyped-def]
    context = FakeContext()
    monkeypatch.setattr(application, "MainWindow", FakeWindow)
    monkeypatch.setattr(QApplication, "exec", lambda self: 7)
    assert application.run_application(qapp, context) == 7
    assert FakeWindow.shown
    assert context.closed


def test_window_failure_is_controlled_and_closes(monkeypatch, qapp) -> None:  # type: ignore[no-untyped-def]
    context = FakeContext()
    messages: list[str] = []

    def fail_window(
        settings: object, controller: object, execution: object, export_service: object
    ) -> None:
        del settings, controller, execution, export_service
        raise RuntimeError("internal/path traceback detail")

    monkeypatch.setattr(application, "MainWindow", fail_window)
    monkeypatch.setattr(
        application.QMessageBox,
        "critical",
        lambda parent, title, text: messages.append(text),
    )
    assert application.run_application(qapp, context) != 0
    assert context.closed
    assert messages
    assert "traceback" not in messages[0].lower()
    assert "internal/path" not in messages[0]


def test_main_context_failure_shows_controlled_error(monkeypatch, qapp) -> None:  # type: ignore[no-untyped-def]
    messages: list[str] = []
    monkeypatch.setattr(application, "create_qt_application", lambda: qapp)
    monkeypatch.setattr(
        application,
        "build_application_context",
        lambda: (_ for _ in ()).throw(RuntimeError("failure")),
    )
    monkeypatch.setattr(
        application.QMessageBox,
        "critical",
        lambda parent, title, text: messages.append(text),
    )
    assert application.main() != 0
    assert messages == [
        "DIP Workbench could not start.\n\nCheck the application log for more information."
    ]
