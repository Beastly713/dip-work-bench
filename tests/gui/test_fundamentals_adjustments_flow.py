"""Focused GUI smoke for fundamentals and basic adjustments."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox

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
from dip_workbench.ui.operations.common import BeforeAfterImageWithCurvePresenter
from dip_workbench.ui.operations.fundamentals import ChannelExtractionPresenter
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
        timeout=3000,
    )


def editor(window: MainWindow) -> GeneratedParameterEditor:
    item = window.parameter_panel.operation_panel._editor
    assert isinstance(item, GeneratedParameterEditor)
    return item


def test_fundamentals_and_adjustments_flow(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, image_io = make_window(qtbot, tmp_path)
    data = np.array(
        [
            [[10, 20, 30], [220, 210, 200]],
            [[80, 120, 160], [250, 10, 40]],
        ],
        dtype=np.uint8,
    )
    source = ImageAsset("colour", data, ColourModel.RGB)
    path = image_io.save(source, tmp_path / "colour.png")
    assert window.open_primary_image_path(path)

    window.open_operation(operation_registry.get("M01-01"))
    wait_result(qtbot, window)
    assert (
        window.operation_controller.active_result.primary_artifact.data.colour_model
        is ColourModel.GRAY
    )  # type: ignore[union-attr]

    window.open_operation(operation_registry.get("M01-02"))
    wait_result(qtbot, window)
    otsu = editor(window).controls["mode"]
    assert isinstance(otsu, QComboBox)
    otsu.setCurrentIndex(otsu.findData("otsu"))
    wait_result(qtbot, window)
    binary = window.operation_controller.active_result.primary_artifact.data  # type: ignore[union-attr]
    assert binary.colour_model is ColourModel.BINARY  # type: ignore[union-attr]
    assert set(np.unique(binary.data)) <= {0, 255}  # type: ignore[union-attr]

    window.open_operation(operation_registry.get("M01-03"))
    wait_result(qtbot, window)
    presenter = window.operation_workspace._result_presenter
    assert isinstance(presenter, ChannelExtractionPresenter)
    assert len(presenter._artifacts) == 3

    window.open_operation(operation_registry.get("M02-02"))
    wait_result(qtbot, window)
    brightness = editor(window).controls["brightness"]
    assert isinstance(brightness, QSpinBox)
    brightness.setValue(25)
    wait_result(qtbot, window)
    assert window.operation_controller.parameter_values["brightness"] == 25

    window.open_operation(operation_registry.get("M03-03"))
    wait_result(qtbot, window)
    gamma = editor(window).controls["gamma"]
    assert isinstance(gamma, QDoubleSpinBox)
    gamma.setValue(0.5)
    wait_result(qtbot, window)
    presenter = window.operation_workspace._result_presenter
    assert isinstance(presenter, BeforeAfterImageWithCurvePresenter)
    image_target = window.operation_workspace.displayed_export_target()
    presenter.curve_toggle.click()
    curve_target = window.operation_workspace.displayed_export_target()
    assert image_target is not None and curve_target is not None
    assert image_target.artifact.key == "gamma_corrected_image"
    assert curve_target.artifact.key == "gamma_curve"
