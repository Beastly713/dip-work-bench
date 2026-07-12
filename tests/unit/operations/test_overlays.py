"""Tests for reduced overlay primitive contracts."""

import math

import pytest

from dip_workbench.core import InputValidationError
from dip_workbench.operations import CircleOverlay, LineOverlay, OverlayData, PointOverlay


def test_overlay_data_accepts_lines_circles_and_points() -> None:
    overlays = OverlayData(
        (
            LineOverlay(0, 1, 2, 3),
            CircleOverlay(4, 5, 6),
            PointOverlay(7, 8, 2),
        )
    )
    assert len(overlays.items) == 3
    assert overlays.items[0].x1 == 0.0  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: LineOverlay(math.nan, 0, 1, 1),
        lambda: LineOverlay(True, 0, 1, 1),
        lambda: CircleOverlay(0, 0, 0),
        lambda: PointOverlay(0, 0, -1),
        lambda: OverlayData((object(),)),  # type: ignore[arg-type]
    ],
)
def test_overlay_data_rejects_invalid_values(factory) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(InputValidationError):
        factory()
