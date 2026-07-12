"""M09-03 Colour-Range Segmentation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

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
    extract_masked,
    mask_metrics,
    mask_overlay,
    range_pair,
    strict_range_validator,
)
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import ApplyCandidate, OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


class ColourRangeExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model is not ColourModel.RGB:
            raise InputValidationError("Colour-range segmentation requires RGB input.")
        r = range_pair(context.parameters.get("red_range"), "Red range")
        g = range_pair(context.parameters.get("green_range"), "Green range")
        b = range_pair(context.parameters.get("blue_range"), "Blue range")
        lower = np.array([r[0], g[0], b[0]], dtype=np.uint8)
        upper = np.array([r[1], g[1], b[1]], dtype=np.uint8)
        context.cancellation_token.raise_if_cancelled()
        mask = cv2.inRange(image.data, lower, upper)
        extracted = extract_masked(image, mask)
        overlay = mask_overlay(image, mask)
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M09-03",
            "input_asset_id": image.id,
            "red_range": r,
            "green_range": g,
            "blue_range": b,
            "colour_space": "RGB",
        }
        return OperationResult(
            MaskArtifact(
                "colour_mask",
                "Colour-Range Mask",
                ImageAsset(
                    f"{Path(image.name).stem}-colour-mask",
                    mask,
                    ColourModel.BINARY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "extracted_region",
                    "Extracted Region",
                    ImageAsset(
                        f"{Path(image.name).stem}-extracted",
                        extracted.data,
                        ColourModel.RGB,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "colour_overlay",
                    "Colour-Range Overlay",
                    ImageAsset(
                        f"{Path(image.name).stem}-colour-overlay",
                        overlay.data,
                        ColourModel.RGB,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
            ),
            metrics=mask_metrics(mask),
            metadata={"input_asset": image},
            apply_candidates=(
                ApplyCandidate("colour_mask", "Colour-Range Mask"),
                ApplyCandidate("extracted_region", "Extracted Region"),
            ),
        )


def create_colour_presenter() -> object:
    from dip_workbench.ui.operations.segmentation import ColourRangePresenter

    return ColourRangePresenter()


COLOUR_RANGE_DEFINITION = OperationDefinition(
    OperationId("M09-03"),
    ModuleId.M09,
    "Colour-Range Segmentation",
    "Segment RGB pixels inside inclusive channel ranges.",
    (InputSpec("image", "Primary Image", accepted_colour_models=frozenset({ColourModel.RGB})),),
    (
        ParameterSpec(
            "red_range",
            "Red Range",
            ParameterType.INTEGER_RANGE,
            (0, 255),
            minimum=0,
            maximum=255,
            validator=strict_range_validator("Red range"),
        ),
        ParameterSpec(
            "green_range",
            "Green Range",
            ParameterType.INTEGER_RANGE,
            (0, 255),
            minimum=0,
            maximum=255,
            validator=strict_range_validator("Green range"),
        ),
        ParameterSpec(
            "blue_range",
            "Blue Range",
            ParameterType.INTEGER_RANGE,
            (0, 255),
            minimum=0,
            maximum=255,
            validator=strict_range_validator("Blue range"),
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.EXPLICIT_CANDIDATES,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    ColourRangeExecutor,
    create_colour_presenter,
)

operation_registry.register(COLOUR_RANGE_DEFINITION)
