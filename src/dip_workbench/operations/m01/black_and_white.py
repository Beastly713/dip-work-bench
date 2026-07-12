"""M01-02 Black-and-White Thresholding."""

from __future__ import annotations

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
from dip_workbench.operations.parameters import (
    ConditionOperator,
    ParameterChoice,
    ParameterCondition,
    ParameterSpec,
    ParameterType,
)
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution.contracts import OperationContext

THRESHOLD_MODES = (ParameterChoice("manual", "Manual"), ParameterChoice("otsu", "Otsu"))
POLARITIES = (
    ParameterChoice("bright_foreground", "Bright foreground"),
    ParameterChoice("dark_foreground", "Dark foreground"),
)


def _gray_data(image: ImageAsset) -> np.ndarray:
    if image.colour_model is ColourModel.RGB:
        return cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
    return np.array(image.data, copy=True, order="C")


class BlackAndWhiteExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
            ColourModel.BINARY,
        }:
            raise InputValidationError("Black-and-White Thresholding requires an image.")
        mode = context.parameters.get("mode")
        threshold = context.parameters.get("threshold")
        polarity = context.parameters.get("polarity")
        if mode not in {"manual", "otsu"} or polarity not in {
            choice.value for choice in POLARITIES
        }:
            raise InputValidationError("Thresholding parameters are invalid.")
        if not isinstance(threshold, int) or isinstance(threshold, bool):
            raise InputValidationError("Threshold must be an integer.")
        gray = _gray_data(image)
        flag = cv2.THRESH_BINARY if polarity == "bright_foreground" else cv2.THRESH_BINARY_INV
        if mode == "otsu":
            used_threshold, binary = cv2.threshold(gray, 0, 255, flag | cv2.THRESH_OTSU)
        else:
            used_threshold, binary = cv2.threshold(gray, threshold, 255, flag)
        output = np.ascontiguousarray(binary, dtype=np.uint8)
        white = int(np.count_nonzero(output == 255))
        total = int(output.size)
        black = total - white
        metrics = {
            "Threshold Used": float(used_threshold),
            "White Pixels": white,
            "Black Pixels": black,
            "White Percentage": white * 100.0 / total,
            "Black Percentage": black * 100.0 / total,
        }
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-binary",
            data=output,
            colour_model=ColourModel.BINARY,
            source_path=image.source_path,
            metadata={
                "operation_id": "M01-02",
                "input_asset_id": image.id,
                "mode": mode,
                "threshold": threshold,
                "polarity": polarity,
                "threshold_used": float(used_threshold),
            },
        )
        return OperationResult(
            MaskArtifact("binary_image", "Binary Image", asset),
            metrics=metrics,
            metadata={"input_asset": image},
        )


def create_black_and_white_presenter() -> object:
    from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter

    return BeforeAfterImageWithMetricsPresenter(result_label="Binary Result")


BLACK_AND_WHITE_DEFINITION = OperationDefinition(
    OperationId("M01-02"),
    ModuleId.M01,
    "Black-and-White Thresholding",
    "Convert an image to a binary mask.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset(
                {ColourModel.RGB, ColourModel.GRAY, ColourModel.BINARY}
            ),
        ),
    ),
    (
        ParameterSpec(
            "mode",
            "Mode",
            ParameterType.ENUM,
            "manual",
            choices=THRESHOLD_MODES,
        ),
        ParameterSpec(
            "threshold",
            "Threshold",
            ParameterType.INTEGER,
            127,
            minimum=0,
            maximum=255,
            enabled_when=ParameterCondition("mode", ConditionOperator.EQUALS, "manual"),
        ),
        ParameterSpec(
            "polarity",
            "Polarity",
            ParameterType.ENUM,
            "bright_foreground",
            choices=POLARITIES,
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    BlackAndWhiteExecutor,
    create_black_and_white_presenter,
)

operation_registry.register(BLACK_AND_WHITE_DEFINITION)
