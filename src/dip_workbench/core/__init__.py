"""Core types for DIP Workbench."""

from dip_workbench.core.errors import (
    CancelledOperation,
    DIPWorkbenchError,
    ExportError,
    InputValidationError,
    OperationExecutionError,
    ParameterValidationError,
    UnsupportedImageError,
    ValidationError,
)
from dip_workbench.core.image import ColourModel, FloatingImage, ImageAsset
from dip_workbench.core.image_conversion import (
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

__all__ = [
    "CancelledOperation",
    "ColourModel",
    "DIPWorkbenchError",
    "ExportError",
    "FloatingImage",
    "ImageAsset",
    "InputValidationError",
    "OperationExecutionError",
    "ParameterValidationError",
    "UnsupportedImageError",
    "ValidationError",
    "bgr_to_rgb",
    "bgra_to_rgba",
    "composite_rgba_on_background",
    "normalize_absolute_for_display",
    "normalize_for_display",
    "normalize_signed_for_display",
    "rgb_to_bgr",
    "rgb_to_grayscale",
    "rgba_to_bgra",
]
