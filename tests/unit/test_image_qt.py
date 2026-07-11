"""Tests for canonical asset to QImage conversion."""

import numpy as np
import pytest
from PySide6.QtGui import QImage

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.ui.image_qt import image_asset_to_qimage


def test_rgb_dimensions_order_and_detachment() -> None:
    data = np.array([[[255, 10, 20], [1, 2, 3]]], dtype=np.uint8)
    asset = ImageAsset(name="rgb", data=data, colour_model=ColourModel.RGB)
    image = image_asset_to_qimage(asset)
    assert image.size().width() == 2 and image.size().height() == 1
    assert image.format() == QImage.Format.Format_RGB888
    colour = image.pixelColor(0, 0)
    assert (colour.red(), colour.green(), colour.blue()) == (255, 10, 20)
    mutable = asset.mutable_copy()
    mutable.fill(0)
    assert image.pixelColor(0, 0).red() == 255


@pytest.mark.parametrize("model", [ColourModel.GRAY, ColourModel.BINARY])
def test_single_channel_display(model: ColourModel) -> None:
    data = np.array([[0, 255]], dtype=np.uint8)
    asset = ImageAsset(name="single", data=data, colour_model=model)
    image = image_asset_to_qimage(asset)
    assert image.format() == QImage.Format.Format_Grayscale8
    assert image.pixelColor(0, 0).red() == 0
    assert image.pixelColor(1, 0).red() == 255


def test_unsupported_values_are_rejected() -> None:
    label = ImageAsset(
        name="label", data=np.zeros((2, 2), dtype=np.int32), colour_model=ColourModel.LABEL
    )
    with pytest.raises(InputValidationError):
        image_asset_to_qimage(label)
    with pytest.raises(InputValidationError):
        image_asset_to_qimage(object())  # type: ignore[arg-type]
