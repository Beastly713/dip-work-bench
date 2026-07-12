"""Focused GUI smoke for segmentation and frequency-domain operations."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QSettings

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
from dip_workbench.ui.operations.frequency import FourierSpectrumPresenter, FrequencyFilterPresenter
from dip_workbench.ui.operations.segmentation import (
    AdaptiveThresholdPresenter,
    ColourRangePresenter,
    RangeThresholdPresenter,
)


def make_window(qtbot, tmp_path):  # type: ignore[no-untyped-def]
    image_io = ImageIOService()
    history = tmp_path / "history"
    history.mkdir()
    controller = DocumentController(
        image_io, ImageTransformService(), DocumentStore(HistorySnapshotStore(history, image_io))
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


def preview(qtbot, window: MainWindow, values: dict[str, object]) -> None:  # type: ignore[no-untyped-def]
    window.operation_controller.set_parameter_values(values)
    window.operation_controller.preview_or_run()
    wait_result(qtbot, window)


def apply_and_undo(qtbot, window: MainWindow) -> None:  # type: ignore[no-untyped-def]
    before_history = len(window.document_controller.document_store.history)
    window.parameter_panel.operation_panel.apply_button.click()
    qtbot.waitUntil(
        lambda: len(window.document_controller.document_store.history) == before_history + 1,
        timeout=5000,
    )
    window.undo_document()
    qtbot.waitUntil(lambda: window.document_controller.current_image is not None, timeout=5000)


def apply_current(qtbot, window: MainWindow) -> None:  # type: ignore[no-untyped-def]
    before_history = len(window.document_controller.document_store.history)
    window.parameter_panel.operation_panel.apply_button.click()
    qtbot.waitUntil(
        lambda: len(window.document_controller.document_store.history) == before_history + 1,
        timeout=5000,
    )


def test_segmentation_and_frequency_flow(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window, image_io = make_window(qtbot, tmp_path)
    tile = np.array(
        [
            [[255, 0, 0], [0, 255, 0], [0, 0, 255], [120, 120, 120]],
            [[220, 40, 40], [40, 220, 40], [40, 40, 220], [180, 180, 180]],
            [[20, 20, 20], [80, 80, 80], [160, 160, 160], [240, 240, 240]],
            [[255, 120, 0], [0, 255, 120], [120, 0, 255], [30, 200, 240]],
        ],
        dtype=np.uint8,
    )
    rgb = np.tile(tile, (4, 4, 1))
    path = image_io.save(ImageAsset("rgb", rgb, ColourModel.RGB), tmp_path / "rgb.png")
    assert window.open_primary_image_path(path)

    window.open_operation(operation_registry.get("M09-02"))
    wait_result(qtbot, window)
    preview(qtbot, window, {"intensity_range": (60, 190), "include_boundaries": False})
    range_presenter = window.operation_workspace._result_presenter
    assert isinstance(range_presenter, RangeThresholdPresenter)
    assert window.operation_workspace.displayed_export_target().artifact.key == "range_mask"  # type: ignore[union-attr]
    range_presenter.toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "range_overlay"  # type: ignore[union-attr]

    window.open_operation(operation_registry.get("M09-03"))
    wait_result(qtbot, window)
    preview(
        qtbot, window, {"red_range": (180, 255), "green_range": (0, 130), "blue_range": (0, 130)}
    )
    colour_presenter = window.operation_workspace._result_presenter
    assert isinstance(colour_presenter, ColourRangePresenter)
    colour_presenter.toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "extracted_region"  # type: ignore[union-attr]
    colour_presenter.tabs.setCurrentIndex(1)
    assert window.operation_workspace.displayed_export_target().artifact.key == "colour_overlay"  # type: ignore[union-attr]
    candidates = window.parameter_panel.operation_panel.candidate_selector
    assert candidates.findData("colour_mask") >= 0
    assert candidates.findData("extracted_region") >= 0

    window.open_operation(operation_registry.get("M09-05"))
    wait_result(qtbot, window)
    preview(qtbot, window, {"block_size": 3, "offset": 1, "include_global_otsu_comparison": True})
    adaptive = window.operation_workspace._result_presenter
    assert isinstance(adaptive, AdaptiveThresholdPresenter)
    adaptive.toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "global_otsu_mask"  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M07-01"))
    wait_result(qtbot, window)
    preview(
        qtbot, window, {"center_spectrum": False, "logarithmic_scale": False, "show_phase": True}
    )
    spectrum = window.operation_workspace._result_presenter
    assert isinstance(spectrum, FourierSpectrumPresenter)
    assert not window.parameter_panel.operation_panel.apply_button.isVisible()
    assert window.operation_workspace.displayed_export_target().artifact.key == "fourier_magnitude"  # type: ignore[union-attr]
    spectrum.toggle.click()
    assert window.operation_workspace.displayed_export_target().artifact.key == "fourier_phase"  # type: ignore[union-attr]

    window.open_operation(operation_registry.get("M07-03"))
    wait_result(qtbot, window)
    preview(qtbot, window, {"cutoff_percent": 25.0})
    low = window.operation_workspace._result_presenter
    assert isinstance(low, FrequencyFilterPresenter)
    low.toggle.click()
    for key in ("low_pass_input_spectrum", "low_pass_mask", "low_pass_filtered_spectrum"):
        low.tabs.setCurrentIndex(low._keys.index(key))
        assert window.operation_workspace.displayed_export_target().artifact.key == key  # type: ignore[union-attr]
    apply_current(qtbot, window)

    window.open_operation(operation_registry.get("M07-04"))
    wait_result(qtbot, window)
    preview(qtbot, window, {"cutoff_percent": 30.0})
    high = window.operation_workspace._result_presenter
    assert isinstance(high, FrequencyFilterPresenter)
    high.toggle.click()
    for key in ("high_pass_input_spectrum", "high_pass_mask", "high_pass_filtered_spectrum"):
        high.tabs.setCurrentIndex(high._keys.index(key))
        assert window.operation_workspace.displayed_export_target().artifact.key == key  # type: ignore[union-attr]
    assert "high_pass_response_signed" not in high._keys
    apply_and_undo(qtbot, window)
