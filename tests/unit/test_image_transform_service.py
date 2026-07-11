import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError, RectangularRegion
from dip_workbench.services import (
    FlipDirection,
    ImageTransformService,
    InterpolationMode,
    RotationCanvasMode,
)


def asset(model: ColourModel = ColourModel.GRAY) -> ImageAsset:
    data = np.arange(24, dtype=np.uint8).reshape(4, 6)
    if model is ColourModel.RGB:
        data = np.repeat(data[..., None], 3, axis=2)
    if model is ColourModel.BINARY:
        data = (data % 2 * 255).astype(np.uint8)
    return ImageAsset(name="photo.png", data=data, colour_model=model)


def test_crop_resize_rotate_flip_and_metadata() -> None:
    service = ImageTransformService()
    source = asset()
    cropped = service.crop(source, RectangularRegion(1, 1, 3, 2))
    assert cropped.shape == (2, 3)
    resized = service.resize(source, width=3, height=2, interpolation=InterpolationMode.AREA)
    assert resized.shape == (2, 3)
    rotated = service.rotate(
        source,
        angle_degrees=90,
        canvas_mode=RotationCanvasMode.EXPANDED,
        interpolation=InterpolationMode.NEAREST,
    )
    assert rotated.shape == (6, 4)
    cropped_rotation = service.rotate(
        source,
        angle_degrees=30,
        canvas_mode=RotationCanvasMode.CROPPED,
        interpolation=InterpolationMode.LINEAR,
    )
    assert cropped_rotation.shape == source.shape
    flipped = service.flip(source, direction=FlipDirection.HORIZONTAL)
    np.testing.assert_array_equal(
        service.flip(flipped, direction=FlipDirection.HORIZONTAL).data, source.data
    )
    assert (
        cropped.id != source.id
        and cropped.metadata["utility_operation_id"] == "U-05"
        and not cropped.data.flags.writeable
    )
    np.testing.assert_array_equal(source.data, asset().data)


def test_binary_and_invalid_parameters() -> None:
    service = ImageTransformService()
    binary = asset(ColourModel.BINARY)
    result = service.resize(binary, width=12, height=8, interpolation=InterpolationMode.NEAREST)
    assert set(np.unique(result.data)) <= {0, 255}
    with pytest.raises(InputValidationError):
        service.resize(binary, width=2, height=2, interpolation=InterpolationMode.LINEAR)
    with pytest.raises(InputValidationError):
        service.rotate(
            binary,
            angle_degrees=float("nan"),
            canvas_mode=RotationCanvasMode.EXPANDED,
            interpolation=InterpolationMode.NEAREST,
        )
    with pytest.raises(InputValidationError):
        service.rotate(
            asset(),
            angle_degrees=20,
            canvas_mode=RotationCanvasMode.EXPANDED,
            interpolation=InterpolationMode.AREA,
        )
