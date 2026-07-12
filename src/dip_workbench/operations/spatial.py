"""Small stateless spatial-filter helpers."""

from __future__ import annotations

import cv2
import numpy as np

from dip_workbench.core import InputValidationError


def validate_odd_kernel_size(value: object, *, allowed: set[int] | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value % 2 == 0:
        raise InputValidationError("Kernel size must be a positive odd integer.")
    if allowed is not None and value not in allowed:
        raise InputValidationError("Kernel size is unsupported.")
    return value


def opencv_border_type(border: object) -> int:
    if border == "replicate":
        return cv2.BORDER_REPLICATE
    if border == "reflect":
        return cv2.BORDER_REFLECT_101
    if border == "constant":
        return cv2.BORDER_CONSTANT
    raise InputValidationError("Border mode is invalid.")


def pad_image(
    data: np.ndarray, kernel_size: int, border: object, constant_value: int = 0
) -> np.ndarray:
    radius = validate_odd_kernel_size(kernel_size) // 2
    mode = opencv_border_type(border)
    if isinstance(constant_value, bool) or not isinstance(constant_value, int):
        raise InputValidationError("Constant border value must be an integer.")
    value = int(np.clip(constant_value, 0, 255))
    return cv2.copyMakeBorder(data, radius, radius, radius, radius, mode, value=value)


def crop_padding(data: np.ndarray, kernel_size: int) -> np.ndarray:
    radius = validate_odd_kernel_size(kernel_size) // 2
    if radius == 0:
        return np.array(data, copy=True, order="C")
    return np.ascontiguousarray(data[radius:-radius, radius:-radius])


def map_float_response_to_uint8(response: np.ndarray, mode: object) -> np.ndarray:
    if mode == "clipped":
        mapped = np.rint(response)
    elif mode == "absolute":
        mapped = np.rint(np.abs(response))
    elif mode == "normalized":
        minimum = float(np.min(response))
        maximum = float(np.max(response))
        if maximum <= minimum:
            return np.zeros(response.shape, dtype=np.uint8)
        mapped = (response - minimum) * (255.0 / (maximum - minimum))
    else:
        raise InputValidationError("Display mapping is invalid.")
    return np.ascontiguousarray(np.clip(mapped, 0, 255).astype(np.uint8))
