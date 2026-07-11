from pathlib import Path

import numpy as np
from PySide6.QtCore import QSettings

from dip_workbench.controllers import DocumentController
from dip_workbench.core import ColourModel, ImageAsset, RectangularRegion
from dip_workbench.services import ImageIOService, ImageTransformService, SettingsService
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.main_window import MainWindow
from dip_workbench.ui.widgets import CanvasInteractionMode


def make_window(qtbot, tmp_path: Path) -> MainWindow:  # type: ignore[no-untyped-def]
    io = ImageIOService()
    history = tmp_path / "history"
    history.mkdir()
    controller = DocumentController(
        io, ImageTransformService(), DocumentStore(HistorySnapshotStore(history, io))
    )
    window = MainWindow(
        SettingsService(QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)), controller
    )
    qtbot.addWidget(window)
    window.show()
    return window


def test_crop_preview_apply_undo_and_region_only(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window = make_window(qtbot, tmp_path)
    source = ImageAsset(
        name="a", data=np.arange(100, dtype=np.uint8).reshape(10, 10), colour_model=ColourModel.GRAY
    )
    window.document_controller.document_store.set_primary_image(source)
    window._display_document(window.document_controller.current_image, fit=True)  # type: ignore[arg-type]
    for key in ("crop", "resize", "rotate", "flip", "select_region"):
        assert window.action_map[key].isEnabled()
    assert all(
        action.text() not in {"Crop…", "Resize…", "Rotate…", "Flip/Mirror…"}
        for action in window.global_toolbar.actions()
    )
    window.open_utility("crop")
    region = RectangularRegion(1, 2, 4, 5)
    window._region_finished(region)
    current = window.document_controller.current_image
    window._preview_transform(window.document_controller.preview_crop)
    assert (
        window.document_controller.current_image is current
        and not window.document_controller.document_store.history
    )
    window.apply_utility_preview()
    assert (
        window.document_controller.current_image.shape == (5, 4)
        and window.document_controller.document_store.history[-1].operation_id == "U-05"
    )
    window.undo_document()
    assert window.document_controller.current_image.shape == (10, 10)
    window.redo_document()
    assert window.document_controller.current_image.shape == (5, 4)


def test_region_finish_clear_and_cancel(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window = make_window(qtbot, tmp_path)
    source = ImageAsset(
        name="a", data=np.zeros((10, 10), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    window.document_controller.document_store.set_primary_image(source)
    window._display_document(window.document_controller.current_image, fit=True)  # type: ignore[arg-type]
    window.open_utility("select_region")
    window._region_finished(RectangularRegion(2, 2, 3, 3))
    assert (
        window.document_controller.selected_region is not None
        and not window.document_controller.document_store.history
    )
    window.operation_workspace.image_canvas.cancel_interaction()
    assert window.operation_workspace.image_canvas.interaction_mode is CanvasInteractionMode.PAN
    window.clear_region_selection()
    assert window.document_controller.selected_region is None
