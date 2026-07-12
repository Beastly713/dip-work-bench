"""Focused tests for M09 segmentation operations."""

import cv2
import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    AdaptiveThresholdExecutor,
    ColourRangeExecutor,
    RangeThresholdExecutor,
)


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


def test_intensity_range_boundaries_validation_and_luminance() -> None:
    gray = ImageAsset("gray", np.array([[80, 100, 180]], dtype=np.uint8), ColourModel.GRAY)
    inc = RangeThresholdExecutor().execute(
        context(gray, {"intensity_range": (80, 180), "include_boundaries": True})
    )
    exc = RangeThresholdExecutor().execute(
        context(gray, {"intensity_range": (80, 180), "include_boundaries": False})
    )
    assert inc.primary_artifact.data.data.tolist() == [[255, 255, 255]]  # type: ignore[union-attr]
    assert exc.primary_artifact.data.data.tolist() == [[0, 255, 0]]  # type: ignore[union-attr]
    with pytest.raises(InputValidationError):
        RangeThresholdExecutor().execute(
            context(gray, {"intensity_range": (100, 100), "include_boundaries": True})
        )
    rgb = ImageAsset("rgb", np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8), ColourModel.RGB)
    result = RangeThresholdExecutor().execute(
        context(rgb, {"intensity_range": (70, 80), "include_boundaries": True})
    )
    expected_gray = cv2.cvtColor(rgb.data, cv2.COLOR_RGB2GRAY)
    np.testing.assert_array_equal(
        result.primary_artifact.data.data,
        np.where((expected_gray >= 70) & (expected_gray <= 80), 255, 0).astype(np.uint8),
    )  # type: ignore[union-attr]


def test_colour_range_uses_rgb_order_extracts_and_preserves_source() -> None:
    data = np.array([[[255, 0, 0], [0, 0, 255]], [[10, 20, 30], [200, 50, 50]]], dtype=np.uint8)
    image = ImageAsset("rgb", data, ColourModel.RGB)
    result = ColourRangeExecutor().execute(
        context(image, {"red_range": (200, 255), "green_range": (0, 60), "blue_range": (0, 60)})
    )
    mask = result.primary_artifact.data.data  # type: ignore[union-attr]
    np.testing.assert_array_equal(mask, np.array([[255, 0], [0, 255]], dtype=np.uint8))
    extracted = result.get_artifact("extracted_region").data.data  # type: ignore[union-attr]
    np.testing.assert_array_equal(extracted[mask != 0], data[mask != 0])
    assert np.all(extracted[mask == 0] == 0)
    np.testing.assert_array_equal(image.data, data)


def test_adaptive_binary_validation_polarity_otsu_and_source_immutable() -> None:
    data = np.tile(np.array([20, 60, 120, 200, 240], dtype=np.uint8), (5, 1))
    image = ImageAsset("gray", data, ColourModel.GRAY)
    bright = AdaptiveThresholdExecutor().execute(
        context(
            image,
            {
                "block_size": 3,
                "offset": 2,
                "polarity": "bright_foreground",
                "include_global_otsu_comparison": False,
            },
        )
    )
    dark = AdaptiveThresholdExecutor().execute(
        context(
            image,
            {
                "block_size": 3,
                "offset": 2,
                "polarity": "dark_foreground",
                "include_global_otsu_comparison": True,
            },
        )
    )
    assert set(np.unique(bright.primary_artifact.data.data).tolist()).issubset({0, 255})  # type: ignore[union-attr]
    np.testing.assert_array_equal(
        bright.primary_artifact.data.data, 255 - dark.primary_artifact.data.data
    )  # type: ignore[union-attr]
    with pytest.raises(InputValidationError):
        AdaptiveThresholdExecutor().execute(
            context(
                image,
                {
                    "block_size": 4,
                    "offset": 2,
                    "polarity": "bright_foreground",
                    "include_global_otsu_comparison": False,
                },
            )
        )
    with pytest.raises(InputValidationError):
        AdaptiveThresholdExecutor().execute(
            context(
                image,
                {
                    "block_size": 7,
                    "offset": 2,
                    "polarity": "bright_foreground",
                    "include_global_otsu_comparison": False,
                },
            )
        )
    assert not any(a.key == "global_otsu_mask" for a in bright.artifacts)
    assert dark.get_artifact("global_otsu_mask").key == "global_otsu_mask"
    np.testing.assert_array_equal(image.data, data)
