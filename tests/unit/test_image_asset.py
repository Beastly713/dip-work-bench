"""Tests for canonical image representations."""

import numpy as np
import pytest

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError


@pytest.mark.parametrize(
    ("model", "data", "channels", "bits"),
    [
        (ColourModel.RGB, np.zeros((3, 4, 3), dtype=np.uint8), 3, 8),
        (ColourModel.GRAY, np.zeros((3, 4), dtype=np.uint8), 1, 8),
        (ColourModel.BINARY, np.array([[0, 255]], dtype=np.uint8), 1, 8),
        (ColourModel.LABEL, np.zeros((3, 4), dtype=np.int32), 1, 32),
    ],
)
def test_valid_assets_and_properties(
    model: ColourModel, data: np.ndarray, channels: int, bits: int
) -> None:
    asset = ImageAsset(name="image", data=data, colour_model=model)
    assert asset.width == data.shape[1]
    assert asset.height == data.shape[0]
    assert asset.channel_count == channels
    assert asset.bit_depth == bits
    assert asset.shape == data.shape
    assert asset.dtype == data.dtype
    assert asset.id


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_valid_floating_image(dtype: np.dtype) -> None:
    data = np.array([[-2.5, 1.25]], dtype=dtype)
    image = FloatingImage(name="response", data=data)
    np.testing.assert_array_equal(image.data, data)
    assert image.data.dtype == dtype


@pytest.mark.parametrize(
    ("model", "data"),
    [
        (ColourModel.RGB, np.zeros((2, 2), dtype=np.uint8)),
        (ColourModel.RGB, np.zeros((2, 2, 3), dtype=np.float32)),
        (ColourModel.GRAY, np.zeros((2, 2, 1), dtype=np.uint8)),
        (ColourModel.BINARY, np.array([[0, 1]], dtype=np.uint8)),
        (ColourModel.LABEL, np.zeros((2, 2), dtype=np.uint8)),
        (ColourModel.GRAY, np.zeros((0, 2), dtype=np.uint8)),
    ],
)
def test_invalid_canonical_arrays_are_rejected(model: ColourModel, data: np.ndarray) -> None:
    with pytest.raises(InputValidationError):
        ImageAsset(name="invalid", data=data, colour_model=model)


def test_integer_floating_intermediate_is_rejected() -> None:
    with pytest.raises(InputValidationError):
        FloatingImage(name="invalid", data=np.zeros((2, 2), dtype=np.int32))


def test_assets_defensively_copy_data_and_metadata() -> None:
    data = np.zeros((2, 2), dtype=np.uint8)
    metadata: dict[str, object] = {"source": "test"}
    asset = ImageAsset(name="gray", data=data, colour_model=ColourModel.GRAY, metadata=metadata)
    data[0, 0] = 255
    metadata["source"] = "changed"
    assert asset.data[0, 0] == 0
    assert asset.metadata["source"] == "test"
    assert not asset.data.flags.writeable
    with pytest.raises(ValueError):
        asset.data[0, 0] = 2


def test_mutable_copy_is_writable_and_independent() -> None:
    asset = ImageAsset(
        name="gray", data=np.zeros((2, 2), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    copied = asset.mutable_copy()
    copied[0, 0] = 255
    assert copied.flags.writeable
    assert asset.data[0, 0] == 0
