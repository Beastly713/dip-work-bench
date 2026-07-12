"""End-to-end GUI acceptance flow for M03-01 Image Negative."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QSettings

from dip_workbench.controllers import DocumentController, OperationWorkspaceState
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.services import (
    FlipDirection,
    ImageIOService,
    ImageTransformService,
    SettingsService,
)
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.main_window import MainWindow
from dip_workbench.ui.operations import (
    ImageNegativeParameterEditor,
    ImageNegativeResultPresenter,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "m03" / "image_negative_input.png"


def make_window(qtbot, tmp_path):  # type: ignore[no-untyped-def]
    image_io = ImageIOService()
    history = tmp_path / "history"
    history.mkdir()
    controller = DocumentController(
        image_io,
        ImageTransformService(),
        DocumentStore(HistorySnapshotStore(history, image_io)),
    )
    manager = OperationExecutionManager()
    window = MainWindow(
        SettingsService(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)),
        controller,
        manager,
    )
    qtbot.addWidget(window)
    window.show()
    return window


def test_image_negative_preview_apply_history_and_export(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window = make_window(qtbot, tmp_path)
    assert window.open_primary_image_path(FIXTURE)
    current = window.document_controller.current_image
    original = window.document_controller.original_image
    assert current is not None and original is not None
    before = current.data.copy()

    # Moving from a visible utility preview restores the real Current Result.
    window.open_utility("flip")
    window._preview_transform(
        window.document_controller.preview_flip, direction=FlipDirection.HORIZONTAL
    )
    assert not np.array_equal(window.operation_workspace.image_canvas.current_asset.data, before)  # type: ignore[union-attr]
    window.action_map["image_negative"].trigger()
    assert np.array_equal(window.operation_workspace.image_canvas.current_asset.data, before)  # type: ignore[union-attr]
    assert window.operation_workspace.operation_header.name_label.text() == "Image Negative"

    editor = window.parameter_panel.operation_panel._editor
    assert isinstance(editor, ImageNegativeParameterEditor)
    assert editor.colour_handling_combo.currentText() == "Luminance only"
    editor.colour_handling_combo.setCurrentIndex(editor.colour_handling_combo.findData("channels"))
    window.parameter_panel.operation_panel.preview_button.click()
    qtbot.waitUntil(
        lambda: window.operation_controller.workspace_state is OperationWorkspaceState.RESULT,
        timeout=3000,
    )
    assert not window.document_controller.document_store.history
    assert np.array_equal(window.document_controller.current_image.data, before)  # type: ignore[union-attr]

    presenter = window.operation_workspace._result_presenter
    assert isinstance(presenter, ImageNegativeResultPresenter)
    assert presenter.input_canvas.current_asset is not None
    assert presenter.result_canvas.current_asset is not None
    assert np.array_equal(presenter.input_canvas.current_asset.data, before)
    assert np.array_equal(presenter.result_canvas.current_asset.data, 255 - before)
    presenter.mapping_toggle.click()
    assert presenter.mapping_curve.isVisibleTo(presenter)

    window.parameter_panel.operation_panel.apply_button.click()
    qtbot.waitUntil(
        lambda: len(window.document_controller.document_store.history) == 1,
        timeout=3000,
    )
    negative = window.document_controller.current_image
    assert negative is not None and np.array_equal(negative.data, 255 - before)
    assert window.document_controller.original_image is original
    entry = window.document_controller.document_store.history[0]
    assert entry.operation_id == "M03-01"
    assert entry.parameters["colour_handling"] == "channels"
    assert entry.metadata["selected_artifact_key"] == "negative_image"

    window.undo_document()
    assert np.array_equal(window.document_controller.current_image.data, before)  # type: ignore[union-attr]
    window.redo_document()
    assert np.array_equal(window.document_controller.current_image.data, 255 - before)  # type: ignore[union-attr]
    assert len(window.document_controller.document_store.history) == 1

    exported = tmp_path / "negative-export"
    assert window.export_displayed_result_path(exported)
    exported = exported.with_suffix(".png")
    reloaded = window.document_controller.image_io.load(exported)
    assert np.array_equal(reloaded.data, window.document_controller.current_image.data)  # type: ignore[union-attr]
