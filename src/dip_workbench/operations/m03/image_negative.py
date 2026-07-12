"""M03-01 Image Negative definition and pure executor."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import CurveArtifact, ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputRole, InputSpec
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution.contracts import OperationContext

COLOUR_HANDLING_CHOICES = (
    ParameterChoice("luminance", "Luminance only"),
    ParameterChoice("channels", "Each RGB channel"),
    ParameterChoice("grayscale", "Grayscale output"),
)


class ImageNegativeExecutor:
    """Create a photographic negative without mutating its input."""

    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Image Negative requires an RGB or grayscale image.")
        handling = context.parameters.get("colour_handling")
        if handling not in {choice.value for choice in COLOUR_HANDLING_CHOICES}:
            raise InputValidationError("Colour Handling is invalid.")

        if image.colour_model is ColourModel.GRAY or handling == "channels":
            output = cv2.bitwise_not(image.data)
            model = image.colour_model
        elif handling == "grayscale":
            gray = cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
            output = cv2.bitwise_not(gray)
            model = ColourModel.GRAY
        else:
            luminance = cv2.cvtColor(image.data, cv2.COLOR_RGB2YCrCb)
            luminance[..., 0] = cv2.bitwise_not(luminance[..., 0])
            output = cv2.cvtColor(luminance, cv2.COLOR_YCrCb2RGB)
            model = ColourModel.RGB
        output = np.ascontiguousarray(output, dtype=np.uint8)
        context.cancellation_token.raise_if_cancelled()
        result_asset = ImageAsset(
            name=f"{Path(image.name).stem}-negative",
            data=output,
            colour_model=model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M03-01",
                "input_asset_id": image.id,
                "colour_handling": handling,
            },
        )
        values = np.arange(256, dtype=np.uint8)
        return OperationResult(
            ImageArtifact("negative_image", "Negative Image", result_asset),
            (
                CurveArtifact(
                    "mapping_curve",
                    "Input–Output Mapping",  # noqa: RUF001
                    {"input": values, "output": 255 - values},
                ),
            ),
            metadata={"input_asset": image},
        )


def create_image_negative_parameter_editor() -> object:
    from dip_workbench.ui.operations.image_negative import ImageNegativeParameterEditor

    return ImageNegativeParameterEditor()


def create_image_negative_presenter() -> object:
    from dip_workbench.ui.operations.image_negative import ImageNegativeResultPresenter

    return ImageNegativeResultPresenter()


IMAGE_NEGATIVE_DEFINITION = OperationDefinition(
    OperationId("M03-01"),
    ModuleId.M03,
    "Image Negative",
    "Create the photographic negative of the selected image.",
    (
        InputSpec(
            "image",
            "Primary Image",
            InputRole.PRIMARY_IMAGE,
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "colour_handling",
            "Colour Handling",
            ParameterType.ENUM,
            "luminance",
            choices=COLOUR_HANDLING_CHOICES,
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    ImageNegativeExecutor,
    create_image_negative_presenter,
    ("negative", "invert", "image inversion", "photographic negative"),
    custom_parameter_factory=create_image_negative_parameter_editor,
)

operation_registry.register(IMAGE_NEGATIVE_DEFINITION)
