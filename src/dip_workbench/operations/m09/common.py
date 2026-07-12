"""Small helpers for M09 segmentation operations."""

from __future__ import annotations

from collections.abc import Callable, Mapping

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.core.errors import InputValidationError


def grayscale_u8(image: ImageAsset) -> np.ndarray:
    gray = (
        cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
        if image.colour_model is ColourModel.RGB
        else image.data
    )
    return np.ascontiguousarray(gray, dtype=np.uint8)


def binary_mask(values: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(np.where(values, 255, 0).astype(np.uint8))


def mask_metrics(mask: np.ndarray) -> dict[str, int | float]:
    selected = int(np.count_nonzero(mask))
    total = int(mask.size)
    rejected = total - selected
    return {
        "Selected Pixels": selected,
        "Rejected Pixels": rejected,
        "Selected Percentage": selected * 100.0 / total,
        "Rejected Percentage": rejected * 100.0 / total,
    }


def mask_overlay(image: ImageAsset, mask: np.ndarray) -> ImageAsset:
    base = (
        cv2.cvtColor(image.data, cv2.COLOR_GRAY2RGB)
        if image.colour_model is ColourModel.GRAY
        else np.array(image.data, copy=True, order="C")
    )
    selected = mask != 0
    overlay = base.astype(np.float32)
    overlay[selected] = np.rint(overlay[selected] * 0.55 + np.array([0, 255, 0]) * 0.45)
    return ImageAsset(
        f"{image.name}-overlay",
        np.ascontiguousarray(np.clip(overlay, 0, 255).astype(np.uint8)),
        ColourModel.RGB,
        source_path=image.source_path,
    )


def extract_masked(image: ImageAsset, mask: np.ndarray) -> ImageAsset:
    selected = mask != 0
    data = np.zeros_like(image.data)
    if image.colour_model is ColourModel.RGB:
        data[selected, :] = image.data[selected, :]
    else:
        data[selected] = image.data[selected]
    return ImageAsset(
        f"{image.name}-extracted", data, image.colour_model, source_path=image.source_path
    )


def range_pair(value: object, label: str) -> tuple[int, int]:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise InputValidationError(f"{label} must contain two thresholds.")
    low, high = value
    if (
        not isinstance(low, int)
        or isinstance(low, bool)
        or not isinstance(high, int)
        or isinstance(high, bool)
        or low >= high
    ):
        raise InputValidationError(f"{label} lower bound must be less than upper bound.")
    return low, high


def strict_range_validator(label: str) -> Callable[[object, Mapping[str, object]], str | None]:
    def _validator(value: object, _values: Mapping[str, object]) -> str | None:
        try:
            range_pair(value, label)
        except InputValidationError as error:
            return str(error)
        return None

    return _validator
