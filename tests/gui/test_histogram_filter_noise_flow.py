"""Focused GUI smoke for histogram, filter and noise operations."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QComboBox

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
from dip_workbench.ui.operations.filters import (
    ConvolutionParameterEditor,
    CustomConvolutionPresenter,
)
from dip_workbench.ui.operations.histograms import (
    HistogramAnalysisPresenter,
    HistogramEqualizationPresenter,
)
from dip_workbench.ui.operations.noise import AddNoisePresenter, NoiseParameterEditor
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


def test_histogram_filter_noise_flow(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, image_io = make_window(qtbot, tmp_path)
    data = np.array(
        [
            [[10, 20, 30], [80, 120, 160], [200, 210, 220]],
            [[30, 10, 200], [120, 100, 80], [240, 220, 200]],
            [[5, 60, 120], [40, 90, 140], [180, 200, 230]],
        ],
        dtype=np.uint8,
    )
    path = image_io.save(ImageAsset("rgb", data, ColourModel.RGB), tmp_path / "rgb.png")
    assert window.open_primary_image_path(path)

    window.open_operation(operation_registry.get("M04-01"))
    wait_result(qtbot, window)
    presenter = window.operation_workspace._result_presenter
    assert isinstance(presenter, HistogramAnalysisPresenter)
    controls = generated(window).controls
    bins = controls["bins"]
    mode = controls["mode"]
    assert isinstance(bins, QComboBox) and isinstance(mode, QComboBox)
    bins.setCurrentIndex(bins.findData(16))
    wait_result(qtbot, window)
    mode.setCurrentIndex(mode.findData("normalized"))
    wait_result(qtbot, window)
    presenter.view_selector.setCurrentIndex(presenter.view_selector.findData("grayscale_histogram"))
    presenter.view_selector.setCurrentIndex(presenter.view_selector.findData("rgb_histogram"))
    presenter.channel_toggles["Green"].setChecked(False)
    assert window.operation_workspace.displayed_export_target().artifact.key == "visible_histogram"  # type: ignore[union-attr]
    assert not window.parameter_panel.operation_panel.apply_button.isVisible()

    window.open_operation(operation_registry.get("M04-02"))
    wait_result(qtbot, window)
    equalization = window.operation_workspace._result_presenter
    assert isinstance(equalization, HistogramEqualizationPresenter)
    equalization.analysis_toggle.click()
    equalization.tabs.setCurrentIndex(2)
    assert (
        window.operation_workspace.displayed_export_target().artifact.key == "equalization_mapping"
    )  # type: ignore[union-attr]
    before_history = len(window.document_controller.document_store.history)
    window.parameter_panel.operation_panel.apply_button.click()
    qtbot.waitUntil(
        lambda: len(window.document_controller.document_store.history) == before_history + 1,
        timeout=5000,
    )

    window.open_operation(operation_registry.get("M05-01"))
    wait_result(qtbot, window)
    method = generated(window).controls["filter_method"]
    assert isinstance(method, QComboBox)
    method.setCurrentIndex(method.findData("median"))
    wait_result(qtbot, window)
    assert window.operation_workspace.displayed_export_target().artifact.key == "filtered_image"  # type: ignore[union-attr]

    window.open_operation(operation_registry.get("M05-05"))
    wait_result(qtbot, window)
    conv_editor = window.parameter_panel.operation_panel._editor
    assert isinstance(conv_editor, ConvolutionParameterEditor)
    conv_presenter = window.operation_workspace._result_presenter
    assert isinstance(conv_presenter, CustomConvolutionPresenter)
    conv_presenter.kernel_toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key in {
        "resolved_kernel",
        "flipped_kernel",
    }  # type: ignore[union-attr]

    window.open_operation(operation_registry.get("M08-01"))
    wait_result(qtbot, window)
    noise_editor = window.parameter_panel.operation_panel._editor
    assert isinstance(noise_editor, NoiseParameterEditor)
    old_seed = window.operation_controller.parameter_values["seed"]
    noise_editor.regenerate_button.click()
    wait_result(qtbot, window)
    assert window.operation_controller.parameter_values["seed"] != old_seed
    noise_presenter = window.operation_workspace._result_presenter
    assert isinstance(noise_presenter, AddNoisePresenter)
    noise_presenter.noise_toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "noise_distribution"  # type: ignore[union-attr]
    before_history = len(window.document_controller.document_store.history)
    noise_presenter.noise_toggle.click()
    window.parameter_panel.operation_panel.apply_button.click()
    qtbot.waitUntil(
        lambda: len(window.document_controller.document_store.history) == before_history + 1,
        timeout=5000,
    )
