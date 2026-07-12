"""M01-01 Colour to Grayscale."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
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
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution.contracts import OperationContext

GRAYSCALE_METHODS = (
    ParameterChoice("luminance", "Luminance"),
    ParameterChoice("average", "Average"),
)


class ColourToGrayscaleExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Colour to Grayscale requires an RGB or grayscale image.")
        method = context.parameters.get("method")
        if method not in {choice.value for choice in GRAYSCALE_METHODS}:
            raise InputValidationError("Grayscale method is invalid.")
        if image.colour_model is ColourModel.GRAY:
            output = np.array(image.data, copy=True, order="C")
        elif method == "luminance":
            output = cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
        else:
            output = (
                np.rint(image.data.astype(np.float32).mean(axis=2)).clip(0, 255).astype(np.uint8)
            )
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-grayscale",
            data=np.ascontiguousarray(output, dtype=np.uint8),
            colour_model=ColourModel.GRAY,
            source_path=image.source_path,
            metadata={
                "operation_id": "M01-01",
                "input_asset_id": image.id,
                "conversion_method": method,
            },
        )
        return OperationResult(
            ImageArtifact("grayscale_image", "Grayscale Image", asset),
            metadata={"input_asset": image},
        )


def create_colour_to_grayscale_presenter() -> object:
    from dip_workbench.ui.operations.common import BeforeAfterImagePresenter

    return BeforeAfterImagePresenter(result_label="Grayscale Result")


COLOUR_TO_GRAYSCALE_DEFINITION = OperationDefinition(
    OperationId("M01-01"),
    ModuleId.M01,
    "Colour to Grayscale",
    "Convert a colour image to grayscale.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "method",
            "Method",
            ParameterType.ENUM,
            "luminance",
            choices=GRAYSCALE_METHODS,
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    ColourToGrayscaleExecutor,
    create_colour_to_grayscale_presenter,
    ("grayscale", "greyscale", "gray", "colour conversion", "rgb to gray", "luminance"),
)

operation_registry.register(COLOUR_TO_GRAYSCALE_DEFINITION)
