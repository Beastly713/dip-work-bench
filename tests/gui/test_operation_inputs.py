"""Tests for generic operation input summaries."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np

from dip_workbench.controllers import DocumentController, OperationController
from dip_workbench.controllers.operation_controller import InputSource
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.operations import (
    ApplyPolicy,
    InputSpec,
    ModuleId,
    OperationDefinition,
    OperationId,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.services import ImageIOService, ImageTransformService
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.widgets import OperationInputStrip


def definition() -> OperationDefinition:
    return OperationDefinition(
        OperationId("M02-01"),
        ModuleId.M02,
        "Synthetic Inputs",
        "Test input summaries.",
        (InputSpec("image", "Image A"),),
        (),
        PreviewPolicy.EXPLICIT,
        ApplyPolicy.NONE,
        PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
        lambda: object(),
        lambda: object(),
    )


def make_controller(tmp_path):  # type: ignore[no-untyped-def]
    history = tmp_path / "history"
    history.mkdir()
    io = ImageIOService()
    store = DocumentStore(HistorySnapshotStore(history, io))
    document = DocumentController(io, ImageTransformService(), store)
    store.set_primary_image(
        ImageAsset(
            name="primary", data=np.zeros((4, 5, 3), dtype=np.uint8), colour_model=ColourModel.RGB
        )
    )
    controller = OperationController(document, OperationExecutionManager())
    controller.select_operation(definition())
    return controller, store


def test_single_image_source_summary_and_selection(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    controller, store = make_controller(tmp_path)
    strip = OperationInputStrip()
    qtbot.addWidget(strip)
    strip.source_changed.connect(controller.set_input_source)
    strip.refresh(controller)
    assert "primary" in strip.summary.text()
    assert strip.original_button.isChecked()
    strip.current_button.click()
    assert controller.input_source is InputSource.CURRENT
    store.clear_active_preview()
    strip.refresh(controller)
    assert "primary" in strip.summary.text()
