"""Canonical immutable image representations."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from uuid import uuid4

import numpy as np

from dip_workbench.core.errors import InputValidationError


class ColourModel(StrEnum):
    """Supported canonical image colour models."""

    RGB = "RGB"
    GRAY = "GRAY"
    BINARY = "BINARY"
    LABEL = "LABEL"


def _immutable_metadata(metadata: Mapping[str, object]) -> Mapping[str, object]:
    try:
        return MappingProxyType(dict(metadata))
    except (TypeError, ValueError) as error:
        raise InputValidationError("Image metadata must be a mapping.") from error


@dataclass(frozen=True, slots=True)
class ImageAsset:
    """Own one validated canonical document image."""

    name: str
    data: np.ndarray
    colour_model: ColourModel
    id: str = field(default_factory=lambda: str(uuid4()))
    source_path: Path | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise InputValidationError("Image asset id must be a non-empty string.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InputValidationError("Image asset name must be a non-empty string.")
        if not isinstance(self.colour_model, ColourModel):
            raise InputValidationError("Image asset colour model is invalid.")
        if not isinstance(self.data, np.ndarray):
            raise InputValidationError("Image data must be a NumPy array.")

        expected = {
            ColourModel.RGB: ((3, 3), np.dtype(np.uint8)),
            ColourModel.GRAY: ((2, 2), np.dtype(np.uint8)),
            ColourModel.BINARY: ((2, 2), np.dtype(np.uint8)),
            ColourModel.LABEL: ((2, 2), np.dtype(np.int32)),
        }
        (minimum_dimensions, maximum_dimensions), expected_dtype = expected[self.colour_model]
        if not minimum_dimensions <= self.data.ndim <= maximum_dimensions:
            raise InputValidationError(f"Invalid shape for {self.colour_model.value} image data.")
        if any(dimension <= 0 for dimension in self.data.shape):
            raise InputValidationError("Image dimensions must be positive.")
        if self.colour_model is ColourModel.RGB and self.data.shape[2] != 3:
            raise InputValidationError("RGB image data must have exactly three channels.")
        if self.data.dtype != expected_dtype:
            raise InputValidationError(
                f"{self.colour_model.value} image data must use {expected_dtype}."
            )
        if self.colour_model is ColourModel.BINARY and not np.isin(self.data, (0, 255)).all():
            raise InputValidationError("Binary image data may contain only 0 and 255.")

        copied_data = np.array(self.data, copy=True, order="C")
        copied_data.setflags(write=False)
        object.__setattr__(self, "data", copied_data)
        if self.source_path is not None:
            try:
                object.__setattr__(self, "source_path", Path(self.source_path))
            except TypeError as error:
                raise InputValidationError("Image source path is invalid.") from error
        object.__setattr__(self, "metadata", _immutable_metadata(self.metadata))

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def height(self) -> int:
        return int(self.data.shape[0])

    @property
    def channel_count(self) -> int:
        return 3 if self.colour_model is ColourModel.RGB else 1

    @property
    def bit_depth(self) -> int:
        return self.data.dtype.itemsize * 8

    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    def mutable_copy(self) -> np.ndarray:
        """Return an independent writable copy of the canonical data."""
        return self.data.copy(order="C")


@dataclass(frozen=True, slots=True)
class FloatingImage:
    """Own a signed or floating-point operation intermediate."""

    name: str
    data: np.ndarray
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise InputValidationError("Floating image name must be a non-empty string.")
        if not isinstance(self.data, np.ndarray):
            raise InputValidationError("Floating image data must be a NumPy array.")
        if self.data.dtype not in (np.dtype(np.float32), np.dtype(np.float64)):
            raise InputValidationError("Floating image data must use float32 or float64.")
        if self.data.ndim < 2 or any(dimension <= 0 for dimension in self.data.shape):
            raise InputValidationError(
                "Floating image dimensions must be positive and at least 2D."
            )
        copied_data = np.array(self.data, copy=True, order="C")
        copied_data.setflags(write=False)
        object.__setattr__(self, "data", copied_data)
        object.__setattr__(self, "metadata", _immutable_metadata(self.metadata))
