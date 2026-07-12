"""Focused tests for M06 derivative operations."""

import cv2
import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    FirstOrderGradientExecutor,
    LaplacianResponseExecutor,
    SobelExecutor,
)
from dip_workbench.operations.m06.common import signed_response_heatmap


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


def gradient_params(method: str) -> dict[str, object]:
    return {"method": method}


def sobel_params(**overrides: object) -> dict[str, object]:
    params: dict[str, object] = {
        "kernel_size": 3,
        "scale": 1.0,
        "threshold_enabled": False,
        "threshold": 100,
    }
    params.update(overrides)
    return params


def laplacian_params(**overrides: object) -> dict[str, object]:
    params: dict[str, object] = {"neighbourhood": "four", "scale": 1.0, "display": "absolute"}
    params.update(overrides)
    return params


def test_central_difference_horizontal_ramp_has_x_response_only_interior() -> None:
    ramp = np.tile(np.arange(7, dtype=np.uint8) * 20, (7, 1))
    result = FirstOrderGradientExecutor().execute(
        context(ImageAsset("ramp", ramp, ColourModel.GRAY), gradient_params("central"))
    )
    gx = result.get_artifact("gradient_x_signed").data.data  # type: ignore[union-attr]
    gy = result.get_artifact("gradient_y_signed").data.data  # type: ignore[union-attr]
    assert np.all(gx[2:-2, 2:-2] > 0)
    np.testing.assert_allclose(gy[2:-2, 2:-2], 0.0)


def test_roberts_and_prewitt_return_finite_shaped_results() -> None:
    data = np.arange(25, dtype=np.uint8).reshape(5, 5)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    for method in ("roberts", "prewitt"):
        result = FirstOrderGradientExecutor().execute(context(image, gradient_params(method)))
        output = result.primary_artifact.data
        assert output.shape == data.shape  # type: ignore[union-attr]
        assert np.isfinite(result.get_artifact("gradient_x_signed").data.data).all()  # type: ignore[union-attr]


def test_sobel_keeps_signed_floating_responses_and_threshold_binary() -> None:
    data = np.tile(np.arange(8, dtype=np.uint8) * 25, (8, 1))
    image = ImageAsset("ramp", data, ColourModel.GRAY)
    result = SobelExecutor().execute(context(image, sobel_params()))
    assert isinstance(result.get_artifact("sobel_x_signed").data, FloatingImage)
    assert isinstance(result.get_artifact("sobel_y_signed").data, FloatingImage)
    thresholded = SobelExecutor().execute(
        context(image, sobel_params(threshold_enabled=True, threshold=80))
    )
    values = np.unique(thresholded.primary_artifact.data.data)  # type: ignore[union-attr]
    assert set(values.tolist()).issubset({0, 255})


def test_constant_image_produces_zero_gradient_and_sobel_magnitude() -> None:
    image = ImageAsset("constant", np.full((6, 6), 90, dtype=np.uint8), ColourModel.GRAY)
    gradient = FirstOrderGradientExecutor().execute(context(image, gradient_params("central")))
    sobel = SobelExecutor().execute(context(image, sobel_params()))
    assert np.count_nonzero(gradient.primary_artifact.data.data) == 0  # type: ignore[union-attr]
    assert np.count_nonzero(sobel.primary_artifact.data.data) == 0  # type: ignore[union-attr]


def test_four_neighbour_laplacian_impulse_matches_kernel_pattern() -> None:
    data = np.zeros((5, 5), dtype=np.uint8)
    data[2, 2] = 255
    image = ImageAsset("impulse", data, ColourModel.GRAY)
    result = LaplacianResponseExecutor().execute(context(image, laplacian_params()))
    response = result.get_artifact("laplacian_signed").data.data  # type: ignore[union-attr]
    expected = cv2.filter2D(
        data.astype(np.float32),
        cv2.CV_32F,
        np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32),
        borderType=cv2.BORDER_REFLECT_101,
    )
    np.testing.assert_array_equal(response, expected)


def test_signed_heatmap_maps_positive_to_red_and_negative_to_blue() -> None:
    heatmap = signed_response_heatmap(np.array([[10.0, -10.0, 0.0]], dtype=np.float32))
    assert heatmap[0, 0, 0] == 255 and heatmap[0, 0, 2] == 0
    assert heatmap[0, 1, 2] == 255 and heatmap[0, 1, 0] == 0
    assert heatmap[0, 2].tolist() == [0, 0, 0]
