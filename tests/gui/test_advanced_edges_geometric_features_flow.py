"""Focused GUI smoke for advanced edges and geometric features."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox

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
from dip_workbench.ui.operations.advanced_edges import DoGEdgePresenter, LoGEdgePresenter
from dip_workbench.ui.operations.geometric_features import GeometricFeaturePresenter
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


def test_advanced_edges_and_geometric_features_flow(qtbot, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    window, image_io = make_window(qtbot, tmp_path)
    data = np.zeros((64, 64), dtype=np.uint8)
    data[16:48, 16:48] = 220
    path = image_io.save(ImageAsset("square", data, ColourModel.GRAY), tmp_path / "square.png")
    assert window.open_primary_image_path(path)

    window.open_operation(operation_registry.get("M10-01"))
    wait_result(qtbot, window)
    controls = generated(window).controls
    low = controls["low_threshold"]
    high = controls["high_threshold"]
    assert isinstance(low, QSpinBox) and isinstance(high, QSpinBox)
    low.setValue(180)
    high.setValue(100)
    qtbot.waitUntil(
        lambda: bool(window.parameter_panel.operation_panel.validation_summary.text()), timeout=5000
    )
    window.operation_controller.set_parameter_values({"low_threshold": 30, "high_threshold": 120})
    window.operation_controller.preview_or_run()
    wait_result(qtbot, window)
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M10-02"))
    wait_result(qtbot, window)
    log_presenter = window.operation_workspace._result_presenter
    assert isinstance(log_presenter, LoGEdgePresenter)
    log_presenter.toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "log_smoothed"  # type: ignore[union-attr]
    log_presenter.tabs.setCurrentIndex(1)
    assert (
        window.operation_workspace.displayed_export_target().artifact.key == "log_response_display"
    )  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M10-03"))
    wait_result(qtbot, window)
    dog_controls = generated(window).controls
    sigma_small = dog_controls["sigma_small"]
    sigma_large = dog_controls["sigma_large"]
    assert isinstance(sigma_small, QDoubleSpinBox) and isinstance(sigma_large, QDoubleSpinBox)
    window.operation_controller.set_parameter_values({"sigma_small": 0.8, "sigma_large": 2.5})
    window.operation_controller.preview_or_run()
    wait_result(qtbot, window)
    dog_presenter = window.operation_workspace._result_presenter
    assert isinstance(dog_presenter, DoGEdgePresenter)
    dog_presenter.toggle.click()
    for key in ("dog_small_blur", "dog_large_blur", "dog_response_display"):
        dog_presenter.tabs.setCurrentIndex(
            [item[1] for item in dog_presenter._tab_specs].index(key)
        )
        assert window.operation_workspace.displayed_export_target().artifact.key == key  # type: ignore[union-attr]
    apply_current(qtbot, window)

    monkeypatch.setattr(
        "dip_workbench.operations.m10.hough_lines.cv2.HoughLinesP",
        lambda *_a, **_k: np.array([[[5, 5, 40, 5]]], dtype=np.int32),
    )
    monkeypatch.setattr(
        "dip_workbench.operations.m10.hough_circles.cv2.HoughCircles",
        lambda *_a, **_k: np.array([[[32.0, 32.0, 10.0]]]),
    )

    for op_id, overlay_key, stage_key, table_key in (
        ("M10-04", "detected_lines", "line_edge_map", "line_detections"),
        ("M10-05", "detected_circles", "circle_preprocessed", "circle_detections"),
        ("M10-06", "detected_corners", "harris_response_display", "corner_detections"),
    ):
        window.open_operation(operation_registry.get(op_id))
        wait_result(qtbot, window)
        presenter = window.operation_workspace._result_presenter
        assert isinstance(presenter, GeometricFeaturePresenter)
        assert window.operation_workspace.displayed_export_target().artifact.key == overlay_key  # type: ignore[union-attr]
        assert not window.parameter_panel.operation_panel.apply_button.isVisible()
        presenter.details_toggle.click()
        assert window.operation_workspace.displayed_export_target().artifact.key == stage_key  # type: ignore[union-attr]
        presenter.tabs.setCurrentIndex(1)
        assert window.operation_workspace.displayed_export_target().artifact.key == table_key  # type: ignore[union-attr]
        presenter.details_toggle.click()
        presenter.viewer.visible_toggle.setChecked(False)
        presenter.viewer.visible_toggle.setChecked(True)

    monkeypatch.setattr(
        "dip_workbench.operations.m10.hough_lines.cv2.HoughLinesP", lambda *_a, **_k: None
    )
    window.open_operation(operation_registry.get("M10-04"))
    wait_result(qtbot, window)
    empty_presenter = window.operation_workspace._result_presenter
    assert isinstance(empty_presenter, GeometricFeaturePresenter)
    assert window.operation_workspace.displayed_export_target().artifact.key == "detected_lines"  # type: ignore[union-attr]
