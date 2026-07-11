"""Tests for colour boundaries and display normalization."""

import numpy as np
import pytest

from dip_workbench.core import (
    InputValidationError,
    bgr_to_rgb,
    bgra_to_rgba,
    composite_rgba_on_background,
    normalize_absolute_for_display,
    normalize_for_display,
    normalize_signed_for_display,
    rgb_to_bgr,
    rgb_to_grayscale,
    rgba_to_bgra,
)


def test_bgr_rgb_conversions_and_round_trip() -> None:
    bgr = np.array([[[10, 20, 30]]], dtype=np.uint8)
    original = bgr.copy()
    rgb = bgr_to_rgb(bgr)
    np.testing.assert_array_equal(rgb, [[[30, 20, 10]]])
    np.testing.assert_array_equal(rgb_to_bgr(rgb), bgr)
    np.testing.assert_array_equal(bgr, original)
    assert rgb.flags.c_contiguous


def test_four_channel_round_trip_preserves_alpha() -> None:
    bgra = np.array([[[10, 20, 30, 41]]], dtype=np.uint8)
    rgba = bgra_to_rgba(bgra)
    np.testing.assert_array_equal(rgba, [[[30, 20, 10, 41]]])
    np.testing.assert_array_equal(rgba_to_bgra(rgba), bgra)


def test_grayscale_uses_rgb_semantics() -> None:
    red = np.array([[[255, 0, 0]]], dtype=np.uint8)
    blue = np.array([[[0, 0, 255]]], dtype=np.uint8)
    red_gray = rgb_to_grayscale(red)
    blue_gray = rgb_to_grayscale(blue)
    assert red_gray.shape == (1, 1)
    assert red_gray.dtype == np.uint8
    assert int(red_gray[0, 0]) > int(blue_gray[0, 0])


@pytest.mark.parametrize(
    ("alpha", "expected"),
    [(255, (20, 40, 60)), (0, (255, 255, 255)), (128, (137, 147, 157))],
)
def test_alpha_compositing(alpha: int, expected: tuple[int, int, int]) -> None:
    rgba = np.array([[[20, 40, 60, alpha]]], dtype=np.uint8)
    actual = composite_rgba_on_background(rgba)[0, 0]
    np.testing.assert_allclose(actual, expected, atol=1)


@pytest.mark.parametrize(
    "data",
    [
        np.zeros((2, 2), dtype=np.uint8),
        np.zeros((2, 2, 4), dtype=np.uint8),
        np.zeros((2, 2, 3), dtype=np.float32),
    ],
)
def test_invalid_colour_conversion_shapes_are_rejected(data: np.ndarray) -> None:
    with pytest.raises(InputValidationError):
        bgr_to_rgb(data)


def test_min_max_constant_absolute_and_signed_normalization() -> None:
    np.testing.assert_array_equal(normalize_for_display(np.array([0.0, 5.0, 10.0])), [0, 128, 255])
    np.testing.assert_array_equal(normalize_for_display(np.full((2, 2), 5)), 0)
    np.testing.assert_array_equal(
        normalize_absolute_for_display(np.array([-2.0, 0.0, 4.0])), [128, 0, 255]
    )
    np.testing.assert_array_equal(
        normalize_signed_for_display(np.array([-4.0, 0.0, 4.0])), [0, 128, 255]
    )
    np.testing.assert_array_equal(normalize_signed_for_display(np.zeros((2, 2))), 128)


@pytest.mark.parametrize(
    "data",
    [
        np.array([np.nan]),
        np.array([np.inf]),
        np.array([1 + 2j]),
        np.array([True]),
        np.array([], dtype=np.float64),
    ],
)
def test_invalid_normalization_input_is_rejected(data: np.ndarray) -> None:
    with pytest.raises(InputValidationError):
        normalize_for_display(data)


def test_normalization_does_not_mutate_input() -> None:
    data = np.array([-2.0, 0.0, 3.0])
    original = data.copy()
    normalize_for_display(data)
    normalize_absolute_for_display(data)
    normalize_signed_for_display(data)
    np.testing.assert_array_equal(data, original)
