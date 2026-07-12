"""Focused tests for M05 filtering operations."""

import cv2
import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import BlurFiltersExecutor, CustomConvolutionExecutor
from dip_workbench.ui.operations.filters import resize_kernel_centered


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


BASE_BLUR = {
    "kernel_size": 3,
    "gaussian_sigma": 0.0,
    "border": "replicate",
    "constant_value": 0,
}


@pytest.mark.parametrize("method", ["box", "gaussian", "median", "minimum", "maximum"])
def test_filter_modes_preserve_shape_model_and_input(method: str) -> None:
    data = np.array([[0, 20, 40], [60, 120, 180], [200, 220, 255]], dtype=np.uint8)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    result = BlurFiltersExecutor().execute(context(image, {"filter_method": method, **BASE_BLUR}))
    output = result.primary_artifact.data
    assert output.shape == image.shape  # type: ignore[union-attr]
    assert output.colour_model is ColourModel.GRAY  # type: ignore[union-attr]
    np.testing.assert_array_equal(image.data, data)


def conv_params(**overrides: object) -> dict[str, object]:
    params: dict[str, object] = {
        "preset": "custom",
        "kernel_size": 3,
        "kernel": ((0, 0, 0), (1, 0, 0), (0, 0, 0)),
        "normalize_kernel": False,
        "colour_handling": "grayscale",
        "border": "constant",
        "constant_value": 0,
        "display_mapping": "clipped",
    }
    params.update(overrides)
    return params


def test_custom_convolution_flips_asymmetric_kernel() -> None:
    data = np.arange(25, dtype=np.uint8).reshape(5, 5)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    result = CustomConvolutionExecutor().execute(context(image, conv_params()))
    kernel = np.array(conv_params()["kernel"], dtype=float)
    expected = cv2.filter2D(
        data.astype(float), cv2.CV_64F, np.flip(kernel, axis=(0, 1)), borderType=cv2.BORDER_CONSTANT
    )
    np.testing.assert_array_equal(
        result.primary_artifact.data.data, np.clip(np.rint(expected), 0, 255).astype(np.uint8)
    )  # type: ignore[union-attr]


def test_zero_sum_normalization_errors() -> None:
    image = ImageAsset("gray", np.zeros((3, 3), dtype=np.uint8), ColourModel.GRAY)
    with pytest.raises(InputValidationError):
        CustomConvolutionExecutor().execute(
            context(
                image, conv_params(kernel=((0, 0, 0), (1, -1, 0), (0, 0, 0)), normalize_kernel=True)
            )
        )


def test_mapping_modes_obey_invariants_and_source_immutable() -> None:
    data = np.array([[10, 20], [30, 40]], dtype=np.uint8)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    kernel = ((0, 0, 0), (0, -2, 0), (0, 0, 0))
    clipped = CustomConvolutionExecutor().execute(
        context(image, conv_params(kernel=kernel, display_mapping="clipped"))
    )
    absolute = CustomConvolutionExecutor().execute(
        context(image, conv_params(kernel=kernel, display_mapping="absolute"))
    )
    normalized = CustomConvolutionExecutor().execute(
        context(image, conv_params(kernel=kernel, display_mapping="normalized"))
    )
    assert clipped.primary_artifact.data.data.min() == 0  # type: ignore[union-attr]
    assert absolute.primary_artifact.data.data.max() > 0  # type: ignore[union-attr]
    assert normalized.primary_artifact.data.data.min() == 0  # type: ignore[union-attr]
    assert normalized.primary_artifact.data.data.max() == 255  # type: ignore[union-attr]
    np.testing.assert_array_equal(image.data, data)


def test_custom_kernel_resize_preserves_centered_values() -> None:
    kernel = ((0.0, 0.0, 0.0), (0.0, 7.5, 0.0), (0.0, 0.0, 0.0))
    larger = resize_kernel_centered(kernel, 5)
    assert len(larger) == 5
    assert all(len(row) == 5 for row in larger)
    assert larger[2][2] == 7.5
    restored = resize_kernel_centered(larger, 3)
    assert restored == kernel
