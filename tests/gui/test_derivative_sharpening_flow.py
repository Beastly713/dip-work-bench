"""Focused GUI smoke for derivative and sharpening operations."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox

from dip_workbench.controllers import DocumentController, OperationWorkspaceState
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.operations import operation_registry
from dip_workbench.services import (
    ExportService,
    ImageIOService,
    ImageTransformService,
    SettingsService,
)
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.main_window import MainWindow
from dip_workbench.ui.operations.derivatives import (
    DerivativeTriplePresenter,
    LaplacianResponsePresenter,
)
from dip_workbench.ui.operations.sharpening import (
    DetailSharpeningPresenter,
    LaplacianSharpeningPresenter,
)
from dip_workbench.ui.widgets import GeneratedParameterEditor


def make_window(qtbot, tmp_path):  # type: ignore[no-untyped-def]
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
    return window, image_io


def wait_result(qtbot, window: MainWindow) -> None:  # type: ignore[no-untyped-def]
    qtbot.waitUntil(
        lambda: window.operation_controller.workspace_state is OperationWorkspaceState.RESULT,
        timeout=5000,
    )


def generated(window: MainWindow) -> GeneratedParameterEditor:
    editor = window.parameter_panel.operation_panel._editor
    assert isinstance(editor, GeneratedParameterEditor)
    return editor


def apply_current(qtbot, window: MainWindow) -> None:  # type: ignore[no-untyped-def]
    before_history = len(window.document_controller.document_store.history)
    window.parameter_panel.operation_panel.apply_button.click()
    qtbot.waitUntil(
        lambda: len(window.document_controller.document_store.history) == before_history + 1,
        timeout=5000,
    )


def test_derivative_and_sharpening_flow(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, image_io = make_window(qtbot, tmp_path)
    data = np.array(
        [
            [[10, 20, 30], [60, 90, 120], [140, 160, 180], [220, 230, 240]],
            [[30, 40, 50], [80, 120, 160], [120, 140, 180], [200, 210, 220]],
            [[60, 70, 90], [90, 130, 170], [150, 150, 120], [180, 190, 210]],
            [[80, 60, 40], [120, 100, 80], [160, 140, 120], [240, 220, 200]],
        ],
        dtype=np.uint8,
    )
    path = image_io.save(ImageAsset("rgb", data, ColourModel.RGB), tmp_path / "rgb.png")
    assert window.open_primary_image_path(path)

    window.open_operation(operation_registry.get("M06-01"))
    wait_result(qtbot, window)
    gradient = window.operation_workspace._result_presenter
    assert isinstance(gradient, DerivativeTriplePresenter)
    method = generated(window).controls["method"]
    assert isinstance(method, QComboBox)
    method.setCurrentIndex(method.findData("prewitt"))
    wait_result(qtbot, window)
    for key in ("gradient_x_display", "gradient_y_display", "gradient_magnitude"):
        gradient.selector.setCurrentIndex(gradient.selector.findData(key))
        assert window.operation_workspace.displayed_export_target().artifact.key == key  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M06-02"))
    wait_result(qtbot, window)
    threshold_enabled = generated(window).controls["threshold_enabled"]
    assert isinstance(threshold_enabled, QCheckBox)
    threshold_enabled.setChecked(True)
    wait_result(qtbot, window)
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M06-03"))
    wait_result(qtbot, window)
    lap_response = window.operation_workspace._result_presenter
    assert isinstance(lap_response, LaplacianResponsePresenter)
    display = generated(window).controls["display"]
    assert isinstance(display, QComboBox)
    display.setCurrentIndex(display.findData("signed_heatmap"))
    wait_result(qtbot, window)
    lap_response.details_toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "laplacian_kernel"  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M06-04"))
    wait_result(qtbot, window)
    lap_sharp = window.operation_workspace._result_presenter
    assert isinstance(lap_sharp, LaplacianSharpeningPresenter)
    assert lap_sharp.supports_before_after_comparison()
    assert lap_sharp.activate_before_after_comparison()
    lap_sharp.details_toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "laplacian_display"  # type: ignore[union-attr]
    lap_sharp.tabs.setCurrentIndex(1)
    assert window.operation_workspace.displayed_export_target().artifact.key == "laplacian_kernel"  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M06-05"))
    wait_result(qtbot, window)
    unsharp = window.operation_workspace._result_presenter
    assert isinstance(unsharp, DetailSharpeningPresenter)
    assert unsharp.supports_before_after_comparison()
    unsharp.stages_toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "blurred_image"  # type: ignore[union-attr]
    unsharp.tabs.setCurrentIndex(1)
    assert window.operation_workspace.displayed_export_target().artifact.key == "detail_display"  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M06-06"))
    wait_result(qtbot, window)
    high_boost = window.operation_workspace._result_presenter
    assert isinstance(high_boost, DetailSharpeningPresenter)
    boost = generated(window).controls["boost"]
    assert isinstance(boost, QDoubleSpinBox)
    boost.setValue(2.0)
    wait_result(qtbot, window)
    apply_current(qtbot, window)
