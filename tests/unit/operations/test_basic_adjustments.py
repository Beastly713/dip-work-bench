"""Focused algorithm tests for basic adjustments."""

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import BrightnessContrastExecutor, GammaCorrectionExecutor


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


def test_brightness_contrast_identity_and_clipping() -> None:
    image = ImageAsset("gray", np.array([[0, 100, 255]], dtype=np.uint8), ColourModel.GRAY)
    identity = BrightnessContrastExecutor().execute(
        context(image, {"brightness": 0, "contrast": 1.0})
    )
    clipped = BrightnessContrastExecutor().execute(
        context(image, {"brightness": 100, "contrast": 2.0})
    )
    np.testing.assert_array_equal(identity.primary_artifact.data.data, image.data)  # type: ignore[union-attr]
    np.testing.assert_array_equal(clipped.primary_artifact.data.data, [[100, 255, 255]])  # type: ignore[union-attr]


def test_gamma_identity() -> None:
    image = ImageAsset("gray", np.array([[0, 64, 128, 255]], dtype=np.uint8), ColourModel.GRAY)
    result = GammaCorrectionExecutor().execute(context(image, {"gamma": 1.0}))
    np.testing.assert_array_equal(result.primary_artifact.data.data, image.data)  # type: ignore[union-attr]


def test_gamma_below_and_above_one_change_middle_intensity() -> None:
    image = ImageAsset("gray", np.array([[128]], dtype=np.uint8), ColourModel.GRAY)
    bright = GammaCorrectionExecutor().execute(context(image, {"gamma": 0.5}))
    dark = GammaCorrectionExecutor().execute(context(image, {"gamma": 2.0}))
    assert int(bright.primary_artifact.data.data[0, 0]) > 128  # type: ignore[union-attr]
    assert int(dark.primary_artifact.data.data[0, 0]) < 128  # type: ignore[union-attr]
