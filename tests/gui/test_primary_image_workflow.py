"""GUI tests for the connected primary-image workflow."""

from pathlib import Path

import numpy as np
from PySide6.QtCore import QSettings

from dip_workbench.controllers import DocumentController
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.services import ImageIOService, SettingsService
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.main_window import MainWindow, PageIndex


def window_with_source(qtbot, tmp_path: Path) -> tuple[MainWindow, Path]:  # type: ignore[no-untyped-def]
    image_io = ImageIOService()
    history = tmp_path / "history"
    history.mkdir()
    controller = DocumentController(
        image_io, DocumentStore(HistorySnapshotStore(history, image_io))
    )
    window = MainWindow(
        SettingsService(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)),
        controller,
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
    assert not window.home_page.sample_image_button.isEnabled()
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
    for key in ("compare", "export_result", "add_report"):
        assert not window.action_map[key].isEnabled()
