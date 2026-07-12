"""Focused overlay contracts for Hough and Harris style results."""

import math
from dataclasses import dataclass
from numbers import Real
from typing import TypeAlias

from dip_workbench.core import InputValidationError


def _coordinate(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InputValidationError(f"{label} must be numeric.")
    number = float(value)
    if not math.isfinite(number):
        raise InputValidationError(f"{label} must be finite.")
    return number


@dataclass(frozen=True, slots=True)
class LineOverlay:
    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        for name in ("x1", "y1", "x2", "y2"):
            object.__setattr__(self, name, _coordinate(getattr(self, name), name))


@dataclass(frozen=True, slots=True)
class CircleOverlay:
    center_x: float
    center_y: float
    radius: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "center_x", _coordinate(self.center_x, "center_x"))
        object.__setattr__(self, "center_y", _coordinate(self.center_y, "center_y"))
        radius = _coordinate(self.radius, "radius")
        if radius <= 0:
            raise InputValidationError("Circle radius must be positive.")
        object.__setattr__(self, "radius", radius)


@dataclass(frozen=True, slots=True)
class PointOverlay:
    x: float
    y: float
    radius: float = 3.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _coordinate(self.x, "x"))
        object.__setattr__(self, "y", _coordinate(self.y, "y"))
        radius = _coordinate(self.radius, "radius")
        if radius <= 0:
            raise InputValidationError("Point radius must be positive.")
        object.__setattr__(self, "radius", radius)


OverlayPrimitive: TypeAlias = LineOverlay | CircleOverlay | PointOverlay


@dataclass(frozen=True, slots=True)
class OverlayData:
    items: tuple[OverlayPrimitive, ...]

    def __post_init__(self) -> None:
        items = tuple(self.items)
        if any(not isinstance(item, (LineOverlay, CircleOverlay, PointOverlay)) for item in items):
            raise InputValidationError("Overlay data contains an unsupported primitive.")
        object.__setattr__(self, "items", items)
