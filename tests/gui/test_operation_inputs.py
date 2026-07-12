"""Tests for generic operation input summaries and auxiliary persistence."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np

from dip_workbench.controllers import DocumentController, OperationController
from dip_workbench.core import ColourModel, ImageAsset, RectangularRegion
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.operations import (
    ApplyPolicy,
    InputRole,
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
        (
            InputSpec("image", "Image A", InputRole.PRIMARY_IMAGE),
            InputSpec(
                "reference",
                "Image B",
                InputRole.REFERENCE_IMAGE,
                accepted_colour_models=frozenset({ColourModel.RGB}),
                same_dimensions_as="image",
            ),
            InputSpec(
                "dataset",
                "Dataset",
                InputRole.DATASET,
                multiple=True,
                minimum_count=2,
                maximum_count=None,
            ),
            InputSpec(
                "seeds", "Seed Points", InputRole.SEED_POINTS, required=False, minimum_count=0
            ),
            InputSpec(
                "region",
                "Region Selection",
                InputRole.REGION_SELECTION,
                required=False,
                minimum_count=0,
            ),
        ),
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


def test_image_load_clear_restore_and_validation(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    controller, store = make_controller(tmp_path)
    strip = OperationInputStrip()
    qtbot.addWidget(strip)
    reference = ImageAsset(
        name="reference", data=np.zeros((4, 5, 3), dtype=np.uint8), colour_model=ColourModel.RGB
    )
    controller.set_additional_input("reference", reference)
    strip.refresh(controller)
    assert "reference" in strip.additional_summaries["reference"].text()
    controller.select_operation(definition())
    assert controller.additional_inputs["reference"] is reference
    bad = ImageAsset(
        name="bad", data=np.zeros((3, 3), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    controller.set_additional_input("reference", bad)
    assert "reference" in controller.input_errors
    controller.clear_additional_input("reference")
    assert "reference" not in controller.additional_inputs and not store.auxiliary_inputs


def test_dataset_and_interactive_summaries(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    controller, _ = make_controller(tmp_path)
    strip = OperationInputStrip()
    qtbot.addWidget(strip)
    images = tuple(
        ImageAsset(
            name=f"x{i}", data=np.zeros((4, 5, 3), dtype=np.uint8), colour_model=ColourModel.RGB
        )
        for i in range(2)
    )
    controller.set_additional_input("dataset", images)
    controller.set_additional_input("seeds", ((1, 2), (3, 4), (5, 6)))
    controller.set_additional_input("region", RectangularRegion(1, 2, 3, 2))
    strip.refresh(controller)
    assert "2 images" in strip.additional_summaries["dataset"].text()
    assert "3 selected" in strip.additional_summaries["seeds"].text()
    assert "x=1" in strip.additional_summaries["region"].text()
