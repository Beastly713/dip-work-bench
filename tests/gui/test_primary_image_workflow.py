"""GUI tests for the connected primary-image workflow."""

from pathlib import Path

import numpy as np
from PySide6.QtCore import QMimeData, QSettings, QUrl
from PySide6.QtWidgets import QFileDialog

from dip_workbench.controllers import DocumentController
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.services import (
    ExportService,
    ImageIOService,
    ImageTransformService,
    SettingsService,
)
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.main_window import MainWindow, PageIndex


def window_with_source(qtbot, tmp_path: Path) -> tuple[MainWindow, Path]:  # type: ignore[no-untyped-def]
    image_io = ImageIOService()
    history = tmp_path / "history"
    history.mkdir()
    controller = DocumentController(
        image_io,
        ImageTransformService(),
        DocumentStore(HistorySnapshotStore(history, image_io)),
    )
    window = MainWindow(
        SettingsService(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)),
        controller,
        OperationExecutionManager(),
        ExportService(image_io),
    )
    qtbot.addWidget(window)
    window.show()
    source = tmp_path / "source.png"
    image_io.save(
        ImageAsset(
            name="source",
            data=np.full((8, 12, 3), (10, 20, 30), dtype=np.uint8),
            colour_model=ColourModel.RGB,
        ),
        source,
    )
    return window, source


def test_open_display_save_home_and_actions(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    assert window.action_map["open"].isEnabled()
    assert window.home_page.open_image_button.isEnabled()
    assert not hasattr(window.home_page, "sample_image_button")
    assert window.open_primary_image_path(source)
    assert window.page_stack.currentIndex() == PageIndex.OPERATION
    assert (
        window.operation_workspace.image_canvas.current_asset
        is window.document_controller.current_image
    )
    assert source.name in window.windowTitle()
    assert "12 × 8" in window.workbench_status_bar.left_label.text()  # noqa: RUF001
    assert window.settings.get("paths/last_open_directory", "", str) == str(tmp_path)
    output = tmp_path / "saved.png"
    assert window.save_current_image_path(output) and output.exists()
    assert not window.document_controller.document_store.history
    window.show_home_page()
    window.home_page.continue_button.click()
    assert window.page_stack.currentIndex() == PageIndex.OPERATION


def test_reset_undo_redo_and_cancelled_replacement(qtbot, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    assert window.open_primary_image_path(source)
    window.document_controller.document_store.apply_image(
        ImageAsset(
            name="changed",
            data=np.zeros((8, 12, 3), dtype=np.uint8),
            colour_model=ColourModel.RGB,
        ),
        operation_id="test",
        operation_name="Test",
    )
    window.refresh_document_actions()
    assert window.action_map["undo"].isEnabled()
    window.reset_document()
    window.undo_document()
    assert window.action_map["redo"].isEnabled()
    window.redo_document()
    current = window.document_controller.current_image
    monkeypatch.setattr(window, "_confirm_replacement", lambda: False)
    assert not window.open_primary_image_path(source)
    assert window.document_controller.current_image is current
    for key in ("compare", "add_report"):
        assert not window.action_map[key].isEnabled()
    assert window.action_map["export_result"].isEnabled()


def test_home_open_uses_dialog_and_stale_copy_is_gone(qtbot, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    calls: list[bool] = []
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args: (calls.append(True) or str(source), "PNG (*.png)"),
    )
    window.home_page.open_image_button.click()
    assert calls and window.document_controller.has_document
    assert window.home_page.empty_message_label.text() == (
        "No image loaded. Open an image or drag one here to begin."
    )


def test_cancel_and_corrupt_replacement_preserve_complete_state(
    qtbot, tmp_path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    assert window.open_primary_image_path(source)
    store = window.document_controller.document_store
    store.apply_image(
        ImageAsset(
            name="changed",
            data=np.zeros((8, 12, 3), dtype=np.uint8),
            colour_model=ColourModel.RGB,
        ),
        operation_id="change",
        operation_name="Change",
    )
    store.undo()

    def state() -> tuple[object, ...]:
        return (
            store.original_image,
            store.current_image,
            store.history,
            store.redo_history,
            window.operation_workspace.image_canvas.current_asset,
            window.windowTitle(),
            window.home_page.current_document_label.text(),
        )

    before = state()
    monkeypatch.setattr(window, "_confirm_replacement", lambda: False)
    assert not window.open_primary_image_path(source)
    assert state() == before
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"bad")
    monkeypatch.setattr(window, "_confirm_replacement", lambda: True)
    monkeypatch.setattr(window, "_show_open_error", lambda message: None)
    assert not window.open_primary_image_path(corrupt)
    assert state() == before
    assert not window.open_primary_image_path(tmp_path / "unsupported.gif")
    assert state() == before


def test_save_suffix_filters_failure_and_state_preservation(qtbot, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    assert window.open_primary_image_path(source)
    store = window.document_controller.document_store
    current, original, history = store.current_image, store.original_image, store.history
    no_suffix = tmp_path / "no-suffix"
    assert window.save_current_image_path(no_suffix)
    assert no_suffix.with_suffix(".png").exists()
    assert window.settings.get("paths/last_export_directory", "", str) == str(tmp_path)
    assert (store.current_image, store.original_image, store.history) == (
        current,
        original,
        history,
    )
    monkeypatch.setattr(window, "_show_save_error", lambda message: None)
    assert not window.save_current_image_path(tmp_path / "missing" / "x.png")
    assert (store.current_image, store.original_image, store.history) == (
        current,
        original,
        history,
    )

    captured: list[str] = []
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda parent, title, path, filters: (captured.append(filters) or "", ""),
    )
    window.save_current_image_dialog()
    assert "JPEG" in captured[-1]
    binary = ImageAsset(
        name="mask", data=np.array([[0, 255]], dtype=np.uint8), colour_model=ColourModel.BINARY
    )
    store.set_primary_image(binary)
    window._display_document(store.current_image, fit=True)  # type: ignore[arg-type]
    window.save_current_image_dialog()
    assert "JPEG" not in captured[-1]


def test_canvas_actions_and_pixel_status_for_all_models(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    assert window.open_primary_image_path(source)
    canvas = window.operation_workspace.image_canvas
    window.action_map["actual_size"].trigger()
    assert abs(canvas.zoom_percent - 100) < 0.1
    window.action_map["zoom_in"].trigger()
    assert canvas.zoom_percent > 100
    window.action_map["zoom_out"].trigger()
    window.action_map["fit"].trigger()
    assert canvas.is_fit_to_view
    canvas.pixel_hovered.emit(1, 2, (10, 20, 30))
    assert "RGB:" in window.workbench_status_bar.centre_label.text()
    for model, value, expected in (
        (ColourModel.GRAY, 80, "Value: 80"),
        (ColourModel.BINARY, 255, "Foreground"),
        (ColourModel.BINARY, 0, "Background"),
    ):
        asset = ImageAsset(
            name="value",
            data=np.full((2, 2), value, dtype=np.uint8),
            colour_model=model,
        )
        window.document_controller.document_store.set_primary_image(asset)
        window._display_document(asset, fit=True)
        canvas.pixel_hovered.emit(0, 0, value)
        assert expected in window.workbench_status_bar.centre_label.text()
    canvas.pixel_left.emit()
    assert window.workbench_status_bar.centre_label.text() == ""


class FakeWindowDrop:
    def __init__(self, mime: QMimeData) -> None:
        self._mime = mime
        self.accepted = False

    def mimeData(self) -> QMimeData:
        return self._mime

    def acceptProposedAction(self) -> None:
        self.accepted = True


def test_local_drop_opens_and_remote_drop_is_ignored(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, source = window_with_source(qtbot, tmp_path)
    local_mime = QMimeData()
    local_mime.setUrls([QUrl.fromLocalFile(str(source))])
    local_event = FakeWindowDrop(local_mime)
    window.dropEvent(local_event)  # type: ignore[arg-type]
    assert local_event.accepted and window.document_controller.has_document
    current = window.document_controller.current_image
    remote_mime = QMimeData()
    remote_mime.setUrls([QUrl("https://example.com/other.png")])
    remote_event = FakeWindowDrop(remote_mime)
    window.dropEvent(remote_event)  # type: ignore[arg-type]
    assert not remote_event.accepted
    assert window.document_controller.current_image is current
