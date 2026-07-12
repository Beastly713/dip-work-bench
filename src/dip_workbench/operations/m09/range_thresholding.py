"""M09-02 Intensity-Range Thresholding."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, MaskArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m09.common import (
    binary_mask,
    grayscale_u8,
    mask_metrics,
    mask_overlay,
    range_pair,
    strict_range_validator,
)
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


class RangeThresholdExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError(
                "Intensity-range thresholding requires RGB or grayscale input."
            )
        lower, upper = range_pair(context.parameters.get("intensity_range"), "Intensity range")
        include = bool(context.parameters.get("include_boundaries"))
        gray = grayscale_u8(image)
        context.cancellation_token.raise_if_cancelled()
        selected = (gray >= lower) & (gray <= upper) if include else (gray > lower) & (gray < upper)
        mask = binary_mask(selected)
        overlay = mask_overlay(image, mask)
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M09-02",
            "input_asset_id": image.id,
            "lower_threshold": lower,
            "upper_threshold": upper,
            "include_boundaries": include,
            "colour_conversion": "RGB2GRAY" if image.colour_model is ColourModel.RGB else "none",
        }
        return OperationResult(
            MaskArtifact(
                "range_mask",
                "Intensity-Range Mask",
                ImageAsset(
                    f"{Path(image.name).stem}-range-mask",
                    mask,
                    ColourModel.BINARY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "range_overlay",
                    "Selected-Range Overlay",
                    ImageAsset(
                        overlay.name,
                        overlay.data,
                        overlay.colour_model,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
            ),
            metrics=mask_metrics(mask),
            metadata={"input_asset": image},
        )


def create_range_presenter() -> object:
    from dip_workbench.ui.operations.segmentation import RangeThresholdPresenter

    return RangeThresholdPresenter()


RANGE_THRESHOLD_DEFINITION = OperationDefinition(
    OperationId("M09-02"),
    ModuleId.M09,
    "Intensity-Range Thresholding",
    "Segment pixels whose grayscale intensity falls inside a selected range.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "intensity_range",
            "Intensity Range",
            ParameterType.INTEGER_RANGE,
            (80, 180),
            minimum=0,
            maximum=255,
            validator=strict_range_validator("Intensity range"),
        ),
        ParameterSpec("include_boundaries", "Include Boundaries", ParameterType.BOOLEAN, True),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    RangeThresholdExecutor,
    create_range_presenter,
    (
        "range threshold",
        "intensity range",
        "multiple threshold",
        "band threshold",
        "gray range segmentation",
    ),
)

operation_registry.register(RANGE_THRESHOLD_DEFINITION)
