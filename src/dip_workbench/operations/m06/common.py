"""Small M06 derivative and sharpening helpers."""

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


def normalized_magnitude_image(response: np.ndarray) -> np.ndarray:
    maximum = float(np.max(response))
    if maximum <= 0:
        return np.zeros(response.shape, dtype=np.uint8)
    return np.ascontiguousarray(np.rint(response / maximum * 255.0).clip(0, 255).astype(np.uint8))


def signed_response_image(response: np.ndarray) -> np.ndarray:
    max_abs = float(np.max(np.abs(response)))
    if max_abs == 0:
        return np.full(response.shape, 128, dtype=np.uint8)
    mapped = 128.0 + response / max_abs * 127.0
    return np.ascontiguousarray(np.rint(mapped).clip(0, 255).astype(np.uint8))


def signed_response_heatmap(response: np.ndarray) -> np.ndarray:
    max_abs = float(np.max(np.abs(response)))
    output = np.zeros((*response.shape, 3), dtype=np.uint8)
    if max_abs == 0:
        return output
    positive = np.rint(np.clip(response, 0, None) / max_abs * 255).astype(np.uint8)
    negative = np.rint(np.clip(-response, 0, None) / max_abs * 255).astype(np.uint8)
    output[..., 0] = positive
    output[..., 2] = negative
    return np.ascontiguousarray(output)


def clipped_uint8_plane(plane: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(np.rint(plane).clip(0, 255).astype(np.uint8))


def laplacian_kernel(neighbourhood: object) -> np.ndarray:
    if neighbourhood == "four":
        return np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    if neighbourhood == "eight":
        return np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype=np.float32)
    raise ValueError("Unsupported Laplacian neighbourhood.")


def luminance_working_plane(image: ImageAsset) -> tuple[np.ndarray, np.ndarray | None, ColourModel]:
    if image.colour_model is ColourModel.RGB:
        ycc = cv2.cvtColor(image.data, cv2.COLOR_RGB2YCrCb)
        return ycc[..., 0].astype(np.float32), ycc, ColourModel.RGB
    return image.data.astype(np.float32), None, ColourModel.GRAY


def rebuild_from_luminance(
    plane: np.ndarray, ycc: np.ndarray | None, model: ColourModel
) -> np.ndarray:
    clipped = clipped_uint8_plane(plane)
    if model is ColourModel.RGB and ycc is not None:
        rebuilt = np.array(ycc, copy=True, order="C")
        rebuilt[..., 0] = clipped
        return np.ascontiguousarray(cv2.cvtColor(rebuilt, cv2.COLOR_YCrCb2RGB))
    return np.ascontiguousarray(clipped)


def gaussian_detail_components(
    plane: np.ndarray, *, kernel_size: int, sigma: float
) -> tuple[np.ndarray, np.ndarray]:
    blur = cv2.GaussianBlur(
        plane.astype(np.float32),
        (kernel_size, kernel_size),
        sigma,
        borderType=cv2.BORDER_REFLECT_101,
    )
    return blur, plane.astype(np.float32) - blur
