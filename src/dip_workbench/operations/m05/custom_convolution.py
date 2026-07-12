"""M05-05 Custom Convolution."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, MatrixArtifact
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
from dip_workbench.operations.spatial import (
    map_float_response_to_uint8,
    opencv_border_type,
    validate_odd_kernel_size,
)

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

PRESETS = (
    ParameterChoice("identity", "Identity"),
    ParameterChoice("weighted_average", "Weighted Average"),
    ParameterChoice("custom", "Custom"),
)
CONV_KERNEL_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7))
COLOUR_CHOICES = (
    ParameterChoice("per_channel", "Per channel"),
    ParameterChoice("grayscale", "Grayscale"),
)
MAPPING_CHOICES = tuple(
    ParameterChoice(v, label)
    for v, label in (("clipped", "Clipped"), ("absolute", "Absolute"), ("normalized", "Normalized"))
)
BORDER_CHOICES = tuple(
    ParameterChoice(v, label)
    for v, label in (("replicate", "Replicate"), ("reflect", "Reflect"), ("constant", "Constant"))
)


def identity_kernel(size: int) -> tuple[tuple[float, ...], ...]:
    array = np.zeros((size, size), dtype=float)
    array[size // 2, size // 2] = 1.0
    return tuple(tuple(float(v) for v in row) for row in array)


def weighted_average_kernel(size: int) -> tuple[tuple[float, ...], ...]:
    coeffs = {
        3: np.array([1, 2, 1], dtype=float),
        5: np.array([1, 4, 6, 4, 1], dtype=float),
        7: np.array([1, 6, 15, 20, 15, 6, 1], dtype=float),
    }[size]
    kernel = np.outer(coeffs, coeffs)
    kernel /= kernel.sum()
    return tuple(tuple(float(v) for v in row) for row in kernel)


def resolve_kernel(parameters: Mapping[str, object]) -> np.ndarray:
    size = validate_odd_kernel_size(parameters.get("kernel_size"), allowed={3, 5, 7})
    preset = parameters.get("preset")
    raw: object
    if preset == "identity":
        raw = identity_kernel(size)
    elif preset == "weighted_average":
        raw = weighted_average_kernel(size)
    elif preset == "custom":
        raw = parameters.get("kernel")
    else:
        raise InputValidationError("Convolution preset is invalid.")
    array = np.asarray(raw, dtype=object)
    if array.shape != (size, size):
        raise InputValidationError("Kernel must be square and match kernel size.")
    values = np.empty((size, size), dtype=np.float64)
    for index, value in np.ndenumerate(array):
        if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
            raise InputValidationError("Kernel values must be finite numeric data.")
        number = float(value)
        if not np.isfinite(number):
            raise InputValidationError("Kernel values must be finite numeric data.")
        values[index] = number
    if parameters.get("normalize_kernel"):
        total = float(values.sum())
        if abs(total) < 1e-12:
            raise InputValidationError(
                "Kernel sum is zero; disable normalization for zero-sum kernels."
            )
        values = values / total
    return values


class CustomConvolutionExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Custom convolution requires RGB or grayscale input.")
        params = dict(context.parameters)
        kernel = resolve_kernel(params)
        flipped = np.flip(kernel, axis=(0, 1))
        colour_handling = params.get("colour_handling")
        source = image.data
        model = image.colour_model
        if colour_handling == "grayscale":
            source = (
                cv2.cvtColor(source, cv2.COLOR_RGB2GRAY)
                if image.colour_model is ColourModel.RGB
                else source
            )
            model = ColourModel.GRAY
        elif colour_handling != "per_channel":
            raise InputValidationError("Colour handling is invalid.")
        constant_value = params.get("constant_value")
        if not isinstance(constant_value, int) or isinstance(constant_value, bool):
            raise InputValidationError("Constant value must be an integer.")
        response = cv2.filter2D(
            source.astype(np.float64),
            cv2.CV_64F,
            flipped,
            borderType=opencv_border_type(params.get("border")),
        )
        if params.get("border") == "constant":
            # filter2D cannot pass a custom constant value; emulate it by pre-padding.
            radius = kernel.shape[0] // 2
            padded = cv2.copyMakeBorder(
                source.astype(np.float64),
                radius,
                radius,
                radius,
                radius,
                cv2.BORDER_CONSTANT,
                value=constant_value,
            )
            response = cv2.filter2D(padded, cv2.CV_64F, flipped, borderType=cv2.BORDER_CONSTANT)[
                radius:-radius, radius:-radius
            ]
        output = map_float_response_to_uint8(response, params.get("display_mapping"))
        context.cancellation_token.raise_if_cancelled()
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-convolution",
            data=output,
            colour_model=model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M05-05",
                "input_asset_id": image.id,
                "preset": params.get("preset"),
                "kernel_size": kernel.shape[0],
                "normalize_kernel": params.get("normalize_kernel"),
                "colour_handling": colour_handling,
                "border": params.get("border"),
                "display_mapping": params.get("display_mapping"),
            },
        )
        return OperationResult(
            ImageArtifact("convolution_result", "Convolution Result", asset),
            (
                MatrixArtifact("resolved_kernel", "Resolved Kernel", kernel.tolist()),
                MatrixArtifact("flipped_kernel", "Flipped Kernel Used", flipped.tolist()),
            ),
            metrics={
                "Raw Response Minimum": float(np.min(response)),
                "Raw Response Maximum": float(np.max(response)),
                "Kernel Sum": float(kernel.sum()),
            },
            metadata={"input_asset": image},
        )


def create_convolution_parameter_editor() -> object:
    from dip_workbench.ui.operations.filters import ConvolutionParameterEditor

    return ConvolutionParameterEditor()


def create_custom_convolution_presenter() -> object:
    from dip_workbench.ui.operations.filters import CustomConvolutionPresenter

    return CustomConvolutionPresenter()


CUSTOM_CONVOLUTION_DEFINITION = OperationDefinition(
    OperationId("M05-05"),
    ModuleId.M05,
    "Custom Convolution",
    "Apply a custom convolution kernel.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec("preset", "Preset", ParameterType.ENUM, "identity", choices=PRESETS),
        ParameterSpec(
            "kernel_size", "Kernel Size", ParameterType.ENUM, 3, choices=CONV_KERNEL_CHOICES
        ),
        ParameterSpec("kernel", "Kernel", ParameterType.KERNEL, identity_kernel(3)),
        ParameterSpec("normalize_kernel", "Normalize Kernel", ParameterType.BOOLEAN, True),
        ParameterSpec(
            "colour_handling",
            "Colour Handling",
            ParameterType.ENUM,
            "per_channel",
            choices=COLOUR_CHOICES,
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
        ParameterSpec(
            "display_mapping",
            "Display Mapping",
            ParameterType.ENUM,
            "clipped",
            choices=MAPPING_CHOICES,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    CustomConvolutionExecutor,
    create_custom_convolution_presenter,
    custom_parameter_factory=create_convolution_parameter_editor,
)

operation_registry.register(CUSTOM_CONVOLUTION_DEFINITION)
