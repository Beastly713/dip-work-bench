"""Small helpers for M10 edge and geometric feature operations."""

from __future__ import annotations

from collections.abc import Callable, Mapping

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError


def grayscale_u8(image: ImageAsset) -> np.ndarray:
    gray = (
        cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
        if image.colour_model is ColourModel.RGB
        else image.data
    )
    return np.ascontiguousarray(gray, dtype=np.uint8)


def number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputValidationError(f"{label} must be numeric.")
    return float(value)


def int_value(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputValidationError(f"{label} must be an integer.")
    return value


def validate_threshold_pair(low: object, high: object, label: str) -> tuple[float, float]:
    low_value = number(low, f"{label} low threshold")
    high_value = number(high, f"{label} high threshold")
    if low_value < 0 or high_value < 0 or low_value >= high_value:
        raise InputValidationError(f"{label} low threshold must be less than high threshold.")
    return low_value, high_value


def threshold_pair_validator(
    low_key: str, high_key: str, label: str
) -> Callable[[object, Mapping[str, object]], str | None]:
    def _validator(_value: object, values: Mapping[str, object]) -> str | None:
        try:
            validate_threshold_pair(values.get(low_key), values.get(high_key), label)
        except InputValidationError as error:
            return str(error)
        return None

    return _validator


def canny_edge_map(
    gray: np.ndarray,
    *,
    blur_kernel: int = 5,
    sigma: float = 1.0,
    low_threshold: float = 50.0,
    high_threshold: float = 150.0,
    aperture_size: int = 3,
    l2_gradient: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    smoothed = cv2.GaussianBlur(
        gray,
        (blur_kernel, blur_kernel),
        sigmaX=sigma,
        borderType=cv2.BORDER_REFLECT_101,
    )
    edges = cv2.Canny(
        smoothed,
        low_threshold,
        high_threshold,
        apertureSize=aperture_size,
        L2gradient=l2_gradient,
    )
    return smoothed, np.where(edges > 0, 255, 0).astype(np.uint8)


def zero_crossing_mask(response: np.ndarray, minimum_contrast: float) -> np.ndarray:
    local_min = cv2.erode(
        response, np.ones((3, 3), dtype=np.uint8), borderType=cv2.BORDER_REFLECT_101
    )
    local_max = cv2.dilate(
        response, np.ones((3, 3), dtype=np.uint8), borderType=cv2.BORDER_REFLECT_101
    )
    crosses = (local_min < 0) & (local_max > 0)
    contrast = (local_max - local_min) >= float(minimum_contrast)
    return np.ascontiguousarray(np.where(crosses & contrast, 255, 0).astype(np.uint8))


def edge_metrics(mask: np.ndarray) -> dict[str, int | float]:
    count = int(np.count_nonzero(mask))
    return {"Edge Pixels": count, "Edge Percentage": count * 100.0 / mask.size}


def metadata_base(operation_id: str, image: ImageAsset, **items: object) -> dict[str, object]:
    return {"operation_id": operation_id, "input_asset_id": image.id, **items}
