"""M10-03 Difference of Gaussian Edge Detection."""

from __future__ import annotations

from collections.abc import Mapping
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
from dip_workbench.operations.m06.common import signed_response_heatmap
from dip_workbench.operations.m10.common import edge_metrics, grayscale_u8, metadata_base, number
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


def _sigma_validator(_value: object, values: Mapping[str, object]) -> str | None:
    small = values.get("sigma_small")
    large = values.get("sigma_large")
    if (
        not isinstance(small, (int, float))
        or isinstance(small, bool)
        or not isinstance(large, (int, float))
        or isinstance(large, bool)
    ):
        return "Sigma values must be numeric."
    if float(large) <= float(small):
        return "Large sigma must be greater than small sigma."
    return None


class DoGEdgesExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("DoG requires RGB or grayscale input.")
        small = context.parameters.get("sigma_small")
        large = context.parameters.get("sigma_large")
        threshold = context.parameters.get("edge_threshold")
        error = _sigma_validator(None, context.parameters)
        if error:
            raise InputValidationError(error)
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            raise InputValidationError("DoG edge threshold must be numeric.")
        small_value = number(small, "Small sigma")
        large_value = number(large, "Large sigma")
        gray = grayscale_u8(image).astype(np.float32)
        context.cancellation_token.raise_if_cancelled()
        small_blur = cv2.GaussianBlur(
            gray, (0, 0), sigmaX=small_value, borderType=cv2.BORDER_REFLECT_101
        )
        large_blur = cv2.GaussianBlur(
            gray, (0, 0), sigmaX=large_value, borderType=cv2.BORDER_REFLECT_101
        )
        response = small_blur - large_blur
        response[np.isclose(response, 0.0, atol=1e-4)] = 0.0
        edges = np.ascontiguousarray(
            np.where(np.abs(response) > float(threshold), 255, 0).astype(np.uint8)
        )
        context.cancellation_token.raise_if_cancelled()
        meta = metadata_base(
            "M10-03",
            image,
            sigma_small=small_value,
            sigma_large=large_value,
            edge_threshold=float(threshold),
            border="reflect",
        )
        return OperationResult(
            MaskArtifact(
                "dog_edges",
                "DoG Edge Map",
                ImageAsset(
                    f"{Path(image.name).stem}-dog",
                    edges,
                    ColourModel.BINARY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "dog_small_blur",
                    "Small-Sigma Blur",
                    ImageAsset(
                        f"{Path(image.name).stem}-dog-small",
                        np.rint(small_blur).clip(0, 255).astype(np.uint8),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "dog_large_blur",
                    "Large-Sigma Blur",
                    ImageAsset(
                        f"{Path(image.name).stem}-dog-large",
                        np.rint(large_blur).clip(0, 255).astype(np.uint8),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "dog_response_display",
                    "Signed Response",
                    ImageAsset(
                        f"{Path(image.name).stem}-dog-response",
                        signed_response_heatmap(response),
                        ColourModel.RGB,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "dog_response_signed",
                    "Signed DoG Response",
                    FloatingImage("dog-response", response, {**meta, "response_type": "dog"}),
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


def create_dog_presenter() -> object:
    from dip_workbench.ui.operations.advanced_edges import DoGEdgePresenter

    return DoGEdgePresenter()


DOG_EDGES_DEFINITION = OperationDefinition(
    OperationId("M10-03"),
    ModuleId.M10,
    "Difference of Gaussian Edge Detection",
    "Detect edges from a signed difference of Gaussian response.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "sigma_small",
            "Small Sigma",
            ParameterType.FLOAT,
            1.0,
            minimum=0.1,
            maximum=10.0,
            step=0.1,
            validator=_sigma_validator,
        ),
        ParameterSpec(
            "sigma_large",
            "Large Sigma",
            ParameterType.FLOAT,
            2.0,
            minimum=0.2,
            maximum=20.0,
            step=0.1,
            validator=_sigma_validator,
        ),
        ParameterSpec(
            "edge_threshold",
            "Edge Threshold",
            ParameterType.FLOAT,
            5.0,
            minimum=0.0,
            maximum=255.0,
            step=0.5,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    DoGEdgesExecutor,
    create_dog_presenter,
)

operation_registry.register(DOG_EDGES_DEFINITION)
