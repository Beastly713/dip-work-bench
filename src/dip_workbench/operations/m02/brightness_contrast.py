"""M02-02 Brightness and Contrast."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution.contracts import OperationContext


class BrightnessContrastExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Brightness and Contrast requires RGB or grayscale input.")
        brightness = context.parameters.get("brightness")
        contrast = context.parameters.get("contrast")
        if not isinstance(brightness, int) or isinstance(brightness, bool):
            raise InputValidationError("Brightness must be an integer.")
        if not isinstance(contrast, (int, float)) or isinstance(contrast, bool):
            raise InputValidationError("Contrast must be numeric.")
        output = np.rint(image.data.astype(np.float32) * float(contrast) + brightness)
        output = np.clip(output, 0, 255).astype(np.uint8)
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-adjusted",
            data=np.ascontiguousarray(output, dtype=np.uint8),
            colour_model=image.colour_model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M02-02",
                "input_asset_id": image.id,
                "brightness": brightness,
                "contrast": float(contrast),
            },
        )
        return OperationResult(
            ImageArtifact("adjusted_image", "Adjusted Image", asset),
            metadata={"input_asset": image},
        )


def create_brightness_contrast_presenter() -> object:
    from dip_workbench.ui.operations.common import BeforeAfterImagePresenter

    return BeforeAfterImagePresenter(result_label="Adjusted Result")


BRIGHTNESS_CONTRAST_DEFINITION = OperationDefinition(
    OperationId("M02-02"),
    ModuleId.M02,
    "Brightness and Contrast",
    "Apply linear brightness and contrast adjustment.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "brightness", "Brightness", ParameterType.INTEGER, 0, minimum=-255, maximum=255, step=1
        ),
        ParameterSpec(
            "contrast", "Contrast", ParameterType.FLOAT, 1.0, minimum=0.1, maximum=5.0, step=0.05
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    BrightnessContrastExecutor,
    create_brightness_contrast_presenter,
)

operation_registry.register(BRIGHTNESS_CONTRAST_DEFINITION)
