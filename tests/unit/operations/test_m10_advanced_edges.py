"""Focused tests for M10 advanced edge operations."""

import numpy as np
import pytest

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import CannyExecutor, DoGEdgesExecutor, LoGEdgesExecutor


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


CANNY = {
    "blur_kernel": 3,
    "sigma": 1.0,
    "low_threshold": 30,
    "high_threshold": 90,
    "aperture_size": 3,
    "l2_gradient": True,
}
LOG = {"gaussian_kernel": 3, "sigma": 1.0, "neighbourhood": "eight", "zero_crossing_contrast": 1.0}
DOG = {"sigma_small": 1.0, "sigma_large": 2.0, "edge_threshold": 1.0}


def test_canny_binary_mask_and_threshold_validation() -> None:
    data = np.zeros((20, 20), dtype=np.uint8)
    data[:, 10:] = 255
    image = ImageAsset("step", data, ColourModel.GRAY)
    result = CannyExecutor().execute(context(image, CANNY))
    output = result.primary_artifact.data
    assert output.shape == image.shape  # type: ignore[union-attr]
    assert set(np.unique(output.data).tolist()).issubset({0, 255})  # type: ignore[union-attr]
    with pytest.raises(InputValidationError):
        CannyExecutor().execute(
            context(image, {**CANNY, "low_threshold": 100, "high_threshold": 20})
        )


def test_log_constant_has_no_edges_and_step_has_signed_response() -> None:
    constant = ImageAsset("constant", np.full((20, 20), 80, dtype=np.uint8), ColourModel.GRAY)
    empty = LoGEdgesExecutor().execute(context(constant, LOG))
    assert np.count_nonzero(empty.primary_artifact.data.data) == 0  # type: ignore[union-attr]
    step = np.zeros((20, 20), dtype=np.uint8)
    step[:, 10:] = 255
    result = LoGEdgesExecutor().execute(context(ImageAsset("step", step, ColourModel.GRAY), LOG))
    response_artifact = result.get_artifact("log_response_signed")
    assert isinstance(response_artifact.data, FloatingImage)
    assert not response_artifact.exportable
    response = response_artifact.data.data
    assert np.isfinite(response).all()
    assert response.min() < 0 < response.max()
    assert np.count_nonzero(result.primary_artifact.data.data) > 0  # type: ignore[union-attr]


def test_dog_validation_constant_empty_raw_and_immutability() -> None:
    data = np.full((20, 20), 120, dtype=np.uint8)
    image = ImageAsset("constant", data, ColourModel.GRAY)
    with pytest.raises(InputValidationError):
        DoGEdgesExecutor().execute(context(image, {**DOG, "sigma_large": 1.0}))
    result = DoGEdgesExecutor().execute(context(image, {**DOG, "edge_threshold": 0.0}))
    response_artifact = result.get_artifact("dog_response_signed")
    assert isinstance(response_artifact.data, FloatingImage)
    assert not response_artifact.exportable
    assert np.max(np.abs(response_artifact.data.data)) == 0
    assert np.count_nonzero(result.primary_artifact.data.data) == 0  # type: ignore[union-attr]
    np.testing.assert_array_equal(image.data, data)
