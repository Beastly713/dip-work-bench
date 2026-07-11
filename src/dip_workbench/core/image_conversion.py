"""Central colour-boundary and display-normalization helpers."""

import cv2
import numpy as np

from dip_workbench.core.errors import InputValidationError


def _validate_channels(data: np.ndarray, channels: int) -> None:
    if (
        not isinstance(data, np.ndarray)
        or data.dtype != np.uint8
        or data.ndim != 3
        or data.shape[2] != channels
        or data.shape[0] <= 0
        or data.shape[1] <= 0
    ):
        raise InputValidationError(f"Expected a non-empty uint8 image with {channels} channels.")


def bgr_to_rgb(data: np.ndarray) -> np.ndarray:
    _validate_channels(data, 3)
    return np.ascontiguousarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))


def rgb_to_bgr(data: np.ndarray) -> np.ndarray:
    _validate_channels(data, 3)
    return np.ascontiguousarray(cv2.cvtColor(data, cv2.COLOR_RGB2BGR))


def bgra_to_rgba(data: np.ndarray) -> np.ndarray:
    _validate_channels(data, 4)
    return np.ascontiguousarray(cv2.cvtColor(data, cv2.COLOR_BGRA2RGBA))


def rgba_to_bgra(data: np.ndarray) -> np.ndarray:
    _validate_channels(data, 4)
    return np.ascontiguousarray(cv2.cvtColor(data, cv2.COLOR_RGBA2BGRA))


def rgb_to_grayscale(data: np.ndarray) -> np.ndarray:
    _validate_channels(data, 3)
    return np.ascontiguousarray(cv2.cvtColor(data, cv2.COLOR_RGB2GRAY))


def composite_rgba_on_background(
    data: np.ndarray,
    background: tuple[int, int, int] = (255, 255, 255),
) -> np.ndarray:
    _validate_channels(data, 4)
    if (
        len(background) != 3
        or any(isinstance(value, bool) or not isinstance(value, int) for value in background)
        or any(value < 0 or value > 255 for value in background)
    ):
        raise InputValidationError("Alpha background must contain three integers from 0 to 255.")
    alpha = data[..., 3:4].astype(np.float64) / 255.0
    foreground = data[..., :3].astype(np.float64)
    backdrop = np.asarray(background, dtype=np.float64)
    blended = np.rint(foreground * alpha + backdrop * (1.0 - alpha))
    return np.ascontiguousarray(np.clip(blended, 0, 255).astype(np.uint8))


def _real_finite_array(data: np.ndarray) -> np.ndarray:
    if (
        not isinstance(data, np.ndarray)
        or data.size == 0
        or not np.issubdtype(data.dtype, np.number)
        or np.issubdtype(data.dtype, np.bool_)
        or np.issubdtype(data.dtype, np.complexfloating)
    ):
        raise InputValidationError("Display normalization requires a non-empty real numeric array.")
    converted = data.astype(np.float64, copy=True)
    if not np.isfinite(converted).all():
        raise InputValidationError("Display normalization requires finite values.")
    return converted


def _min_max(data: np.ndarray) -> np.ndarray:
    minimum = float(data.min())
    maximum = float(data.max())
    if minimum == maximum:
        return np.zeros(data.shape, dtype=np.uint8)
    normalized = (data - minimum) * (255.0 / (maximum - minimum))
    return np.ascontiguousarray(np.rint(normalized).astype(np.uint8))


def normalize_for_display(data: np.ndarray) -> np.ndarray:
    return _min_max(_real_finite_array(data))


def normalize_absolute_for_display(data: np.ndarray) -> np.ndarray:
    return _min_max(np.abs(_real_finite_array(data)))


def normalize_signed_for_display(data: np.ndarray) -> np.ndarray:
    converted = _real_finite_array(data)
    magnitude = float(np.abs(converted).max())
    if magnitude == 0:
        return np.full(converted.shape, 128, dtype=np.uint8)
    normalized = (converted / magnitude + 1.0) * 127.5
    return np.ascontiguousarray(np.rint(np.clip(normalized, 0, 255)).astype(np.uint8))
