"""M10-01 Canny Edge Detection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
from dip_workbench.operations.m10.common import (
    canny_edge_map,
    edge_metrics,
    grayscale_u8,
    metadata_base,
    threshold_pair_validator,
    validate_threshold_pair,
)
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

BLUR_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7))


class CannyExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Canny requires RGB or grayscale input.")
        blur_kernel = context.parameters.get("blur_kernel")
        aperture_size = context.parameters.get("aperture_size")
        sigma = context.parameters.get("sigma")
        if not isinstance(blur_kernel, int) or blur_kernel not in {3, 5, 7}:
            raise InputValidationError("Canny blur kernel is invalid.")
        if not isinstance(aperture_size, int) or aperture_size not in {3, 5, 7}:
            raise InputValidationError("Canny aperture size is invalid.")
        if not isinstance(sigma, (int, float)) or isinstance(sigma, bool):
            raise InputValidationError("Canny sigma must be numeric.")
        low, high = validate_threshold_pair(
            context.parameters.get("low_threshold"),
            context.parameters.get("high_threshold"),
            "Canny",
        )
        gray = grayscale_u8(image)
        context.cancellation_token.raise_if_cancelled()
        smoothed, edges = canny_edge_map(
            gray,
            blur_kernel=blur_kernel,
            sigma=float(sigma),
            low_threshold=low,
            high_threshold=high,
            aperture_size=aperture_size,
            l2_gradient=bool(context.parameters.get("l2_gradient")),
        )
        context.cancellation_token.raise_if_cancelled()
        meta = metadata_base(
            "M10-01",
            image,
            blur_kernel=blur_kernel,
            sigma=float(sigma),
            low_threshold=int(low),
            high_threshold=int(high),
            aperture_size=aperture_size,
            l2_gradient=bool(context.parameters.get("l2_gradient")),
            border="reflect",
        )
        return OperationResult(
            MaskArtifact(
                "canny_edges",
                "Canny Edge Map",
                ImageAsset(
                    f"{Path(image.name).stem}-canny",
                    np.ascontiguousarray(edges),
                    ColourModel.BINARY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "canny_smoothed",
                    "Smoothed Input",
                    ImageAsset(
                        f"{Path(image.name).stem}-canny-smoothed",
                        np.ascontiguousarray(smoothed),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
            ),
            metrics=edge_metrics(edges),
            metadata={"input_asset": image},
        )


def create_canny_presenter() -> object:
    from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter

    return BeforeAfterImageWithMetricsPresenter(result_label="Canny Edge Map")


CANNY_DEFINITION = OperationDefinition(
    OperationId("M10-01"),
    ModuleId.M10,
    "Canny Edge Detection",
    "Detect edges using Gaussian smoothing and Canny hysteresis.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec("blur_kernel", "Blur Kernel", ParameterType.ENUM, 5, choices=BLUR_CHOICES),
        ParameterSpec(
            "sigma", "Sigma", ParameterType.FLOAT, 1.0, minimum=0.0, maximum=10.0, step=0.1
        ),
        ParameterSpec(
            "low_threshold",
            "Low Threshold",
            ParameterType.INTEGER,
            50,
            minimum=0,
            maximum=255,
            validator=threshold_pair_validator("low_threshold", "high_threshold", "Canny"),
        ),
        ParameterSpec(
            "high_threshold",
            "High Threshold",
            ParameterType.INTEGER,
            150,
            minimum=0,
            maximum=255,
            validator=threshold_pair_validator("low_threshold", "high_threshold", "Canny"),
        ),
        ParameterSpec(
            "aperture_size", "Aperture Size", ParameterType.ENUM, 3, choices=BLUR_CHOICES
        ),
        ParameterSpec("l2_gradient", "L2 Gradient", ParameterType.BOOLEAN, True),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    CannyExecutor,
    create_canny_presenter,
    (
        "canny",
        "canny edges",
        "hysteresis threshold",
        "non maximum suppression",
        "advanced edge detection",
    ),
)

operation_registry.register(CANNY_DEFINITION)
