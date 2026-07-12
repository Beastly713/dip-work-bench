"""Small helpers for M07 frequency-domain operations."""

from __future__ import annotations

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset


def grayscale_float(image: ImageAsset) -> np.ndarray:
    gray = (
        cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
        if image.colour_model is ColourModel.RGB
        else image.data
    )
    return np.ascontiguousarray(gray.astype(np.float32))


def shifted_fft(gray: np.ndarray) -> np.ndarray:
    return np.fft.fftshift(np.fft.fft2(gray))


def inverse_shifted_fft(spectrum: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(np.fft.ifft2(np.fft.ifftshift(spectrum)).real.astype(np.float32))


def normalize_float_display(values: np.ndarray) -> np.ndarray:
    finite = np.nan_to_num(values.astype(np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    minimum = float(finite.min())
    maximum = float(finite.max())
    if maximum == minimum:
        return np.zeros(finite.shape, dtype=np.uint8)
    return np.ascontiguousarray(
        np.rint((finite - minimum) / (maximum - minimum) * 255).clip(0, 255).astype(np.uint8)
    )


def magnitude_display(spectrum: np.ndarray, *, logarithmic: bool) -> np.ndarray:
    magnitude = np.abs(spectrum)
    if logarithmic:
        magnitude = np.log1p(magnitude)
    return normalize_float_display(magnitude)


def phase_display(spectrum: np.ndarray) -> np.ndarray:
    phase = np.angle(spectrum)
    return np.ascontiguousarray(
        np.rint((phase + np.pi) / (2 * np.pi) * 255).clip(0, 255).astype(np.uint8)
    )


def circular_frequency_mask(
    shape: tuple[int, int], cutoff_percent: float, *, pass_type: str
) -> tuple[np.ndarray, float]:
    height, width = shape
    yy, xx = np.ogrid[:height, :width]
    distances = np.sqrt((yy - height // 2) ** 2 + (xx - width // 2) ** 2)
    cutoff_radius = float(distances.max() * cutoff_percent / 100.0)
    low = distances <= cutoff_radius
    if pass_type == "low":
        return low, cutoff_radius
    if pass_type == "high":
        return ~low, cutoff_radius
    raise ValueError("Unsupported frequency mask type.")


def clipped_reconstruction(values: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(np.rint(values).clip(0, 255).astype(np.uint8))
