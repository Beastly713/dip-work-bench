"""M05-01 Blur and Neighbourhood Filters."""

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
from dip_workbench.operations.parameters import (
    ConditionOperator,
    ParameterChoice,
    ParameterCondition,
    ParameterSpec,
    ParameterType,
)
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.spatial import crop_padding, pad_image, validate_odd_kernel_size

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

FILTER_METHODS = tuple(
    ParameterChoice(v, label)
    for v, label in (
        ("box", "Box"),
        ("gaussian", "Gaussian"),
        ("median", "Median"),
        ("minimum", "Minimum"),
        ("maximum", "Maximum"),
    )
)
KERNEL_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7, 9, 11))
BORDER_CHOICES = tuple(
    ParameterChoice(v, label)
    for v, label in (("replicate", "Replicate"), ("reflect", "Reflect"), ("constant", "Constant"))
)


class BlurFiltersExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Blur filters require RGB or grayscale input.")
        method = context.parameters.get("filter_method")
        kernel_size = validate_odd_kernel_size(
            context.parameters.get("kernel_size"), allowed={3, 5, 7, 9, 11}
        )
        sigma = context.parameters.get("gaussian_sigma")
        border = context.parameters.get("border")
        constant_value = context.parameters.get("constant_value")
        if method not in {choice.value for choice in FILTER_METHODS}:
            raise InputValidationError("Filter method is invalid.")
        if not isinstance(sigma, (int, float)) or isinstance(sigma, bool):
            raise InputValidationError("Gaussian sigma must be numeric.")
        if not isinstance(constant_value, int) or isinstance(constant_value, bool):
            raise InputValidationError("Constant value must be an integer.")
        padded = pad_image(image.data, kernel_size, border, constant_value)
        if method == "box":
            filtered = cv2.blur(padded, (kernel_size, kernel_size))
        elif method == "gaussian":
            filtered = cv2.GaussianBlur(padded, (kernel_size, kernel_size), float(sigma))
        elif method == "median":
            filtered = cv2.medianBlur(padded, kernel_size)
        else:
            kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
            filtered = (
                cv2.erode(padded, kernel) if method == "minimum" else cv2.dilate(padded, kernel)
            )
        output = crop_padding(filtered, kernel_size)
        context.cancellation_token.raise_if_cancelled()
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-filtered",
            data=np.ascontiguousarray(output, dtype=np.uint8),
            colour_model=image.colour_model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M05-01",
                "input_asset_id": image.id,
                "filter_method": method,
                "kernel_size": kernel_size,
                "gaussian_sigma": float(sigma),
                "border": border,
                "constant_value": constant_value,
            },
        )
        return OperationResult(
            ImageArtifact("filtered_image", "Filtered Image", asset),
            metadata={"input_asset": image},
        )


def create_blur_filters_presenter() -> object:
    from dip_workbench.ui.operations.common import BeforeAfterImagePresenter

    return BeforeAfterImagePresenter(result_label="Filtered Result")


BLUR_FILTERS_DEFINITION = OperationDefinition(
    OperationId("M05-01"),
    ModuleId.M05,
    "Blur and Neighbourhood Filters",
    "Apply smoothing and neighbourhood filters.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "filter_method", "Filter Method", ParameterType.ENUM, "gaussian", choices=FILTER_METHODS
        ),
        ParameterSpec("kernel_size", "Kernel Size", ParameterType.ENUM, 5, choices=KERNEL_CHOICES),
        ParameterSpec(
            "gaussian_sigma",
            "Gaussian Sigma",
            ParameterType.FLOAT,
            0.0,
            minimum=0.0,
            maximum=10.0,
            step=0.1,
            visible_when=ParameterCondition("filter_method", ConditionOperator.EQUALS, "gaussian"),
        ),
        ParameterSpec("border", "Border", ParameterType.ENUM, "replicate", choices=BORDER_CHOICES),
        ParameterSpec(
            "constant_value",
            "Constant Value",
            ParameterType.INTEGER,
            0,
            minimum=0,
            maximum=255,
            enabled_when=ParameterCondition("border", ConditionOperator.EQUALS, "constant"),
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    BlurFiltersExecutor,
    create_blur_filters_presenter,
    (
        "blur",
        "smoothing",
        "box filter",
        "average filter",
        "gaussian filter",
        "median filter",
        "minimum filter",
        "maximum filter",
        "neighbourhood filter",
    ),
)

operation_registry.register(BLUR_FILTERS_DEFINITION)
