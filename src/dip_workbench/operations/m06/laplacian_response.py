"""M06-03 Laplacian Response."""

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
    grayscale_float,
    laplacian_kernel,
    normalized_magnitude_image,
    signed_response_heatmap,
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
DISPLAYS = (
    ParameterChoice("absolute", "Absolute"),
    ParameterChoice("signed_heatmap", "Signed heatmap"),
)


class LaplacianResponseExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Laplacian response requires RGB or grayscale input.")
        neighbourhood = context.parameters.get("neighbourhood")
        scale = context.parameters.get("scale")
        display = context.parameters.get("display")
        if not isinstance(scale, (int, float)) or isinstance(scale, bool):
            raise InputValidationError("Laplacian scale must be numeric.")
        gray = grayscale_float(image)
        context.cancellation_token.raise_if_cancelled()
        kernel = laplacian_kernel(neighbourhood)
        response = cv2.filter2D(
            gray, cv2.CV_32F, kernel, borderType=cv2.BORDER_REFLECT_101
        ) * float(scale)
        if display == "absolute":
            data = normalized_magnitude_image(np.abs(response))
            model = ColourModel.GRAY
        elif display == "signed_heatmap":
            data = signed_response_heatmap(response)
            model = ColourModel.RGB
        else:
            raise InputValidationError("Laplacian display is invalid.")
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M06-03",
            "input_asset_id": image.id,
            "neighbourhood": neighbourhood,
            "scale": float(scale),
            "display": display,
        }
        asset = ImageAsset(
            f"{Path(image.name).stem}-laplacian",
            data,
            model,
            source_path=image.source_path,
            metadata=meta,
        )
        return OperationResult(
            ImageArtifact("laplacian_response", "Laplacian Response", asset),
            (
                ImageArtifact(
                    "laplacian_signed",
                    "Signed Laplacian",
                    FloatingImage("laplacian", response, {**meta, "response_type": "laplacian"}),
                    exportable=False,
                ),
                MatrixArtifact("laplacian_kernel", "Laplacian Kernel", kernel.tolist()),
            ),
            metrics={
                "Signed Minimum": float(response.min()),
                "Signed Maximum": float(response.max()),
                "Maximum Absolute Response": float(np.max(np.abs(response))),
                "Kernel Sum": float(kernel.sum()),
            },
            metadata={"input_asset": image},
        )


def create_laplacian_response_presenter() -> object:
    from dip_workbench.ui.operations.derivatives import LaplacianResponsePresenter

    return LaplacianResponsePresenter()


LAPLACIAN_RESPONSE_DEFINITION = OperationDefinition(
    OperationId("M06-03"),
    ModuleId.M06,
    "Laplacian Response",
    "Calculate second-order Laplacian response.",
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
            "scale", "Scale", ParameterType.FLOAT, 1.0, minimum=0.1, maximum=5.0, step=0.1
        ),
        ParameterSpec("display", "Display", ParameterType.ENUM, "absolute", choices=DISPLAYS),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    LaplacianResponseExecutor,
    create_laplacian_response_presenter,
)

operation_registry.register(LAPLACIAN_RESPONSE_DEFINITION)
