"""M10-02 Laplacian of Gaussian Edge Detection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, MaskArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m06.common import laplacian_kernel, signed_response_heatmap
from dip_workbench.operations.m10.common import (
    edge_metrics,
    grayscale_u8,
    metadata_base,
    zero_crossing_mask,
)
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

KERNEL_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7, 9, 11))
NEIGHBOURHOODS = (
    ParameterChoice("four", "Four-neighbour"),
    ParameterChoice("eight", "Eight-neighbour"),
)


class LoGEdgesExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("LoG requires RGB or grayscale input.")
        kernel_size = context.parameters.get("gaussian_kernel")
        sigma = context.parameters.get("sigma")
        contrast = context.parameters.get("zero_crossing_contrast")
        if not isinstance(kernel_size, int) or kernel_size not in {3, 5, 7, 9, 11}:
            raise InputValidationError("LoG Gaussian kernel is invalid.")
        if not isinstance(sigma, (int, float)) or isinstance(sigma, bool):
            raise InputValidationError("LoG sigma must be numeric.")
        if not isinstance(contrast, (int, float)) or isinstance(contrast, bool):
            raise InputValidationError("Zero-crossing contrast must be numeric.")
        gray = grayscale_u8(image).astype(np.float32)
        context.cancellation_token.raise_if_cancelled()
        smoothed = cv2.GaussianBlur(
            gray, (kernel_size, kernel_size), sigmaX=float(sigma), borderType=cv2.BORDER_REFLECT_101
        )
        response = cv2.filter2D(
            smoothed,
            cv2.CV_32F,
            laplacian_kernel(context.parameters.get("neighbourhood")),
            borderType=cv2.BORDER_REFLECT_101,
        )
        edges = zero_crossing_mask(response, float(contrast))
        context.cancellation_token.raise_if_cancelled()
        meta = metadata_base(
            "M10-02",
            image,
            gaussian_kernel=kernel_size,
            sigma=float(sigma),
            neighbourhood=context.parameters.get("neighbourhood"),
            zero_crossing_contrast=float(contrast),
            border="reflect",
        )
        return OperationResult(
            MaskArtifact(
                "log_edges",
                "LoG Edge Map",
                ImageAsset(
                    f"{Path(image.name).stem}-log",
                    edges,
                    ColourModel.BINARY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "log_smoothed",
                    "Smoothed Input",
                    ImageAsset(
                        f"{Path(image.name).stem}-log-smoothed",
                        np.rint(smoothed).clip(0, 255).astype(np.uint8),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "log_response_display",
                    "Signed Response",
                    ImageAsset(
                        f"{Path(image.name).stem}-log-response",
                        signed_response_heatmap(response),
                        ColourModel.RGB,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "log_response_signed",
                    "Signed LoG Response",
                    FloatingImage("log-response", response, {**meta, "response_type": "log"}),
                    exportable=False,
                ),
            ),
            metrics={
                "Response Minimum": float(response.min()),
                "Response Maximum": float(response.max()),
                "Maximum Absolute Response": float(np.max(np.abs(response))),
                **edge_metrics(edges),
            },
            metadata={"input_asset": image},
        )


def create_log_presenter() -> object:
    from dip_workbench.ui.operations.advanced_edges import LoGEdgePresenter

    return LoGEdgePresenter()


LOG_EDGES_DEFINITION = OperationDefinition(
    OperationId("M10-02"),
    ModuleId.M10,
    "Laplacian of Gaussian Edge Detection",
    "Detect zero-crossing edges in a Laplacian of Gaussian response.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "gaussian_kernel", "Gaussian Kernel", ParameterType.ENUM, 5, choices=KERNEL_CHOICES
        ),
        ParameterSpec(
            "sigma", "Sigma", ParameterType.FLOAT, 1.0, minimum=0.1, maximum=10.0, step=0.1
        ),
        ParameterSpec(
            "neighbourhood", "Neighbourhood", ParameterType.ENUM, "eight", choices=NEIGHBOURHOODS
        ),
        ParameterSpec(
            "zero_crossing_contrast",
            "Zero-Crossing Contrast",
            ParameterType.FLOAT,
            10.0,
            minimum=0.0,
            maximum=255.0,
            step=1.0,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    LoGEdgesExecutor,
    create_log_presenter,
)

operation_registry.register(LOG_EDGES_DEFINITION)
