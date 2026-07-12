"""Focused algorithm tests for M01 fundamentals."""

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    BlackAndWhiteExecutor,
    ChannelExtractionExecutor,
    ColourToGrayscaleExecutor,
)


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


def test_luminance_and_average_grayscale_known_values() -> None:
    image = ImageAsset(
        "rgb",
        np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]]], dtype=np.uint8),
        ColourModel.RGB,
    )
    luminance = ColourToGrayscaleExecutor().execute(context(image, {"method": "luminance"}))
    average = ColourToGrayscaleExecutor().execute(context(image, {"method": "average"}))
    np.testing.assert_array_equal(luminance.primary_artifact.data.data, [[76, 150, 29]])  # type: ignore[union-attr]
    np.testing.assert_array_equal(average.primary_artifact.data.data, [[85, 85, 85]])  # type: ignore[union-attr]


def test_manual_threshold_binary_values_and_polarity() -> None:
    image = ImageAsset("gray", np.array([[10, 200]], dtype=np.uint8), ColourModel.GRAY)
    bright = BlackAndWhiteExecutor().execute(
        context(image, {"mode": "manual", "threshold": 127, "polarity": "bright_foreground"})
    )
    dark = BlackAndWhiteExecutor().execute(
        context(image, {"mode": "manual", "threshold": 127, "polarity": "dark_foreground"})
    )
    np.testing.assert_array_equal(bright.primary_artifact.data.data, [[0, 255]])  # type: ignore[union-attr]
    np.testing.assert_array_equal(dark.primary_artifact.data.data, [[255, 0]])  # type: ignore[union-attr]
    assert set(np.unique(bright.primary_artifact.data.data)) == {0, 255}  # type: ignore[union-attr]


def test_otsu_reports_threshold_and_counts() -> None:
    image = ImageAsset(
        "gray",
        np.array([[0, 0, 20, 20], [200, 200, 255, 255]], dtype=np.uint8),
        ColourModel.GRAY,
    )
    result = BlackAndWhiteExecutor().execute(
        context(image, {"mode": "otsu", "threshold": 127, "polarity": "bright_foreground"})
    )
    assert 0 <= result.metrics["Threshold Used"] <= 255
    assert result.metrics["White Pixels"] + result.metrics["Black Pixels"] == image.data.size


def test_channel_indexing_is_rgb_not_bgr() -> None:
    image = ImageAsset(
        "rgb",
        np.array([[[10, 20, 30]]], dtype=np.uint8),
        ColourModel.RGB,
    )
    result = ChannelExtractionExecutor().execute(
        context(image, {"channel": "all", "display": "intensity"})
    )
    assert int(result.get_artifact("red_channel").data.data[0, 0]) == 10  # type: ignore[union-attr]
    assert int(result.get_artifact("green_channel").data.data[0, 0]) == 20  # type: ignore[union-attr]
    assert int(result.get_artifact("blue_channel").data.data[0, 0]) == 30  # type: ignore[union-attr]


def test_isolated_colour_zeroes_other_channels() -> None:
    image = ImageAsset(
        "rgb",
        np.array([[[10, 20, 30]]], dtype=np.uint8),
        ColourModel.RGB,
    )
    result = ChannelExtractionExecutor().execute(
        context(image, {"channel": "green", "display": "isolated_colour"})
    )
    np.testing.assert_array_equal(result.primary_artifact.data.data, [[[0, 20, 0]]])  # type: ignore[union-attr]
