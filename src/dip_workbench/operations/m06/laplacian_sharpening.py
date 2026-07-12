"""M06-04 Laplacian Sharpening."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, MatrixArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m06.common import (
    clipped_uint8_plane,
    laplacian_kernel,
    luminance_working_plane,
    rebuild_from_luminance,
    signed_response_image,
)
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

NEIGHBOURHOODS = (
    ParameterChoice("four", "Four-neighbour"),
    ParameterChoice("eight", "Eight-neighbour"),
)
COLOUR_HANDLING = (
    ParameterChoice("preserve_luminance_colour", "Preserve luminance colour"),
    ParameterChoice("grayscale", "Grayscale"),
)


def _working_plane(
    image: ImageAsset, colour_handling: object
) -> tuple[np.ndarray, np.ndarray | None, ColourModel]:
    if colour_handling == "preserve_luminance_colour":
        return luminance_working_plane(image)
    if colour_handling == "grayscale":
        plane = (
            cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
            if image.colour_model is ColourModel.RGB
            else image.data
        )
        return np.ascontiguousarray(plane.astype(np.float32)), None, ColourModel.GRAY
    raise InputValidationError("Colour handling is invalid.")


class LaplacianSharpeningExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Laplacian sharpening requires RGB or grayscale input.")
        neighbourhood = context.parameters.get("neighbourhood")
        strength = context.parameters.get("strength")
        if not isinstance(strength, (int, float)) or isinstance(strength, bool):
            raise InputValidationError("Laplacian sharpening strength must be numeric.")
        plane, ycc, model = _working_plane(image, context.parameters.get("colour_handling"))
        context.cancellation_token.raise_if_cancelled()
        kernel = laplacian_kernel(neighbourhood)
        laplacian = cv2.filter2D(plane, cv2.CV_32F, kernel, borderType=cv2.BORDER_REFLECT_101)
        sharpened_plane = plane - float(strength) * laplacian
        clipped_plane = clipped_uint8_plane(sharpened_plane)
        output = rebuild_from_luminance(sharpened_plane, ycc, model)
        laplacian_display = signed_response_image(laplacian)
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M06-04",
            "input_asset_id": image.id,
            "neighbourhood": neighbourhood,
            "strength": float(strength),
            "colour_handling": context.parameters.get("colour_handling"),
        }
        primary = ImageAsset(
            f"{Path(image.name).stem}-laplacian-sharpened",
            output,
            model,
            source_path=image.source_path,
            metadata=meta,
        )
        display = ImageAsset(
            f"{Path(image.name).stem}-laplacian-response",
            laplacian_display,
            ColourModel.GRAY,
            source_path=image.source_path,
            metadata=meta,
        )
        return OperationResult(
            ImageArtifact("sharpened_image", "Sharpened Image", primary),
            (
                ImageArtifact("laplacian_display", "Laplacian Display", display),
                ImageArtifact(
                    "laplacian_signed",
                    "Signed Laplacian",
                    FloatingImage(
                        "laplacian-sharpening", laplacian, {**meta, "response_type": "laplacian"}
                    ),
                    exportable=False,
                ),
                MatrixArtifact("laplacian_kernel", "Laplacian Kernel", kernel.tolist()),
            ),
            metrics={
                "Laplacian Minimum": float(laplacian_minimum := laplacian.min()),
                "Laplacian Maximum": float(laplacian.max()),
                "Input Standard Deviation": float(np.std(plane)),
                "Output Standard Deviation": float(np.std(clipped_plane)),
            },
            metadata={"input_asset": image, "laplacian_minimum": float(laplacian_minimum)},
        )


def create_laplacian_sharpening_presenter() -> object:
    from dip_workbench.ui.operations.sharpening import LaplacianSharpeningPresenter

    return LaplacianSharpeningPresenter()


LAPLACIAN_SHARPENING_DEFINITION = OperationDefinition(
    OperationId("M06-04"),
    ModuleId.M06,
    "Laplacian Sharpening",
    "Sharpen an image by subtracting a negative-centre Laplacian response.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "neighbourhood", "Neighbourhood", ParameterType.ENUM, "four", choices=NEIGHBOURHOODS
        ),
        ParameterSpec(
            "strength", "Strength", ParameterType.FLOAT, 1.0, minimum=0.1, maximum=3.0, step=0.1
        ),
        ParameterSpec(
            "colour_handling",
            "Colour Handling",
            ParameterType.ENUM,
            "preserve_luminance_colour",
            choices=COLOUR_HANDLING,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    LaplacianSharpeningExecutor,
    create_laplacian_sharpening_presenter,
    ("laplacian sharpening", "second derivative sharpening"),
)

operation_registry.register(LAPLACIAN_SHARPENING_DEFINITION)
