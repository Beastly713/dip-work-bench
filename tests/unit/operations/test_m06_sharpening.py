"""Focused tests for M06 sharpening operations."""

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    HighBoostExecutor,
    LaplacianSharpeningExecutor,
    UnsharpMaskingExecutor,
)
from dip_workbench.operations.m06.common import gaussian_detail_components, laplacian_kernel


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


LAPLACIAN = {"neighbourhood": "four", "strength": 1.0, "colour_handling": "grayscale"}
UNSHARP = {"kernel_size": 3, "sigma": 0.0, "amount": 0.5}
HIGH_BOOST = {"kernel_size": 3, "sigma": 0.0, "boost": 1.5}


def rounded_uint8(values: np.ndarray) -> np.ndarray:
    return np.rint(values).clip(0, 255).astype(np.uint8)


def test_laplacian_sharpening_uses_source_minus_strength_times_laplacian() -> None:
    data = np.array([[20, 30, 20], [30, 120, 30], [20, 30, 20]], dtype=np.uint8)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    result = LaplacianSharpeningExecutor().execute(context(image, LAPLACIAN))
    response = cv2.filter2D(
        data.astype(np.float32),
        cv2.CV_32F,
        laplacian_kernel("four"),
        borderType=cv2.BORDER_REFLECT_101,
    )
    expected = rounded_uint8(data.astype(np.float32) - response)
    np.testing.assert_array_equal(result.primary_artifact.data.data, expected)  # type: ignore[union-attr]


def test_constant_image_remains_unchanged_under_laplacian_sharpening() -> None:
    data = np.full((5, 5), 88, dtype=np.uint8)
    image = ImageAsset("constant", data, ColourModel.GRAY)
    result = LaplacianSharpeningExecutor().execute(context(image, LAPLACIAN))
    np.testing.assert_array_equal(result.primary_artifact.data.data, data)  # type: ignore[union-attr]


def test_unsharp_and_high_boost_follow_detail_formulas() -> None:
    data = np.array([[0, 20, 40], [60, 120, 180], [200, 220, 255]], dtype=np.uint8)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    blur, detail = gaussian_detail_components(data.astype(np.float32), kernel_size=3, sigma=0.0)
    unsharp = UnsharpMaskingExecutor().execute(context(image, UNSHARP))
    high_boost = HighBoostExecutor().execute(context(image, HIGH_BOOST))
    np.testing.assert_array_equal(
        unsharp.primary_artifact.data.data,
        rounded_uint8(data.astype(np.float32) + 0.5 * detail),  # type: ignore[union-attr]
    )
    np.testing.assert_array_equal(
        high_boost.primary_artifact.data.data,
        rounded_uint8(data.astype(np.float32) + 1.5 * detail),  # type: ignore[union-attr]
    )
    np.testing.assert_allclose(unsharp.get_artifact("detail_signed").data.data, detail)  # type: ignore[union-attr]
    assert blur.shape == data.shape


def test_constant_input_has_zero_detail_and_remains_unchanged() -> None:
    data = np.full((7, 7), 130, dtype=np.uint8)
    image = ImageAsset("constant", data, ColourModel.GRAY)
    for executor, params in (
        (UnsharpMaskingExecutor(), UNSHARP),
        (HighBoostExecutor(), HIGH_BOOST),
    ):
        result = executor.execute(context(image, params))
        np.testing.assert_array_equal(result.primary_artifact.data.data, data)  # type: ignore[union-attr]
        assert result.metrics["Detail Standard Deviation"] == 0


def test_rgb_luminance_processing_preserves_shape_model_and_source() -> None:
    data = np.array(
        [[[40, 80, 120], [80, 120, 160]], [[140, 80, 40], [220, 180, 120]]],
        dtype=np.uint8,
    )
    image = ImageAsset("rgb", data, ColourModel.RGB)
    result = UnsharpMaskingExecutor().execute(context(image, UNSHARP))
    output = result.primary_artifact.data
    assert output.colour_model is ColourModel.RGB  # type: ignore[union-attr]
    assert output.shape == image.shape  # type: ignore[union-attr]
    np.testing.assert_array_equal(image.data, data)
    source_ycc = cv2.cvtColor(data, cv2.COLOR_RGB2YCrCb)
    output_ycc = cv2.cvtColor(output.data, cv2.COLOR_RGB2YCrCb)  # type: ignore[union-attr]
    np.testing.assert_array_equal(output_ycc[..., 1:], source_ycc[..., 1:])
