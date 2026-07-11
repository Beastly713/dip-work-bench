"""Reusable full-resolution image geometry."""

from dataclasses import dataclass

from dip_workbench.core.errors import InputValidationError


@dataclass(frozen=True, slots=True)
class RectangularRegion:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
            raise InputValidationError("Region fields must be integers.")
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise InputValidationError("Region origin must be non-negative and size positive.")

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.x2, self.y2

    def fits_within(self, image_width: int, image_height: int) -> bool:
        return self.x2 <= image_width and self.y2 <= image_height
