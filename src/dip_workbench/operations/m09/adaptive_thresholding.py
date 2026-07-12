"""M09-05 Adaptive Thresholding."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import MaskArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m09.common import grayscale_u8
from dip_workbench.operations.m10.common import int_value
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

POLARITIES = (
    ParameterChoice("bright_foreground", "Bright foreground"),
    ParameterChoice("dark_foreground", "Dark foreground"),
)


def _odd_block_validator(value: object, _values: Mapping[str, object]) -> str | None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 1 or value % 2 == 0:
        return "Block size must be odd and greater than 1."
    return None


def _white_black_metrics(mask: np.ndarray) -> dict[str, int | float]:
    white = int(np.count_nonzero(mask))
    total = int(mask.size)
    black = total - white
    return {
        "White Pixels": white,
        "Black Pixels": black,
        "White Percentage": white * 100.0 / total,
        "Black Percentage": black * 100.0 / total,
    }


class AdaptiveThresholdExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Adaptive thresholding requires RGB or grayscale input.")
        block = context.parameters.get("block_size")
        if _odd_block_validator(block, context.parameters):
            raise InputValidationError(
                _odd_block_validator(block, context.parameters) or "Invalid block size."
            )
        block_size = int_value(block, "Block size")
        gray = grayscale_u8(image)
        if block_size > min(gray.shape):
            raise InputValidationError("Block size must fit within the image dimensions.")
        offset = int_value(context.parameters["offset"], "Offset")
        polarity = context.parameters.get("polarity")
        threshold_type = (
            cv2.THRESH_BINARY if polarity == "bright_foreground" else cv2.THRESH_BINARY_INV
        )
        context.cancellation_token.raise_if_cancelled()
        mask = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, threshold_type, block_size, offset
        )
        mask = np.ascontiguousarray(np.where(mask > 0, 255, 0).astype(np.uint8))
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M09-05",
            "input_asset_id": image.id,
            "block_size": block_size,
            "offset": offset,
            "polarity": polarity,
            "include_global_otsu_comparison": bool(
                context.parameters.get("include_global_otsu_comparison")
            ),
        }
        artifacts = []
        metrics = _white_black_metrics(mask)
        if meta["include_global_otsu_comparison"]:
            threshold, otsu = cv2.threshold(gray, 0, 255, threshold_type | cv2.THRESH_OTSU)
            otsu = np.ascontiguousarray(np.where(otsu > 0, 255, 0).astype(np.uint8))
            artifacts.append(
                MaskArtifact(
                    "global_otsu_mask",
                    "Global Otsu Comparison",
                    ImageAsset(
                        f"{Path(image.name).stem}-global-otsu",
                        otsu,
                        ColourModel.BINARY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                )
            )
            metrics["Global Otsu Threshold"] = float(threshold)
        return OperationResult(
            MaskArtifact(
                "adaptive_mask",
                "Adaptive Threshold Mask",
                ImageAsset(
                    f"{Path(image.name).stem}-adaptive-mask",
                    mask,
                    ColourModel.BINARY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            tuple(artifacts),
            metrics=metrics,
            metadata={"input_asset": image},
        )


def create_adaptive_presenter() -> object:
    from dip_workbench.ui.operations.segmentation import AdaptiveThresholdPresenter

    return AdaptiveThresholdPresenter()


ADAPTIVE_THRESHOLD_DEFINITION = OperationDefinition(
    OperationId("M09-05"),
    ModuleId.M09,
    "Adaptive Thresholding",
    "Segment local bright or dark foreground with mean adaptive thresholding.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "block_size",
            "Block Size",
            ParameterType.INTEGER,
            11,
            minimum=3,
            maximum=51,
            step=2,
            validator=_odd_block_validator,
        ),
        ParameterSpec("offset", "Offset", ParameterType.INTEGER, 2, minimum=-50, maximum=50),
        ParameterSpec(
            "polarity", "Polarity", ParameterType.ENUM, "bright_foreground", choices=POLARITIES
        ),
        ParameterSpec(
            "include_global_otsu_comparison",
            "Include Global Otsu Comparison",
            ParameterType.BOOLEAN,
            False,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    AdaptiveThresholdExecutor,
    create_adaptive_presenter,
)

operation_registry.register(ADAPTIVE_THRESHOLD_DEFINITION)
