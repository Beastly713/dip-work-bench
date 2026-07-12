"""Focused tests for M10 geometric feature operations."""

import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    CircleOverlay,
    HarrisCornersExecutor,
    HoughCirclesExecutor,
    HoughLinesExecutor,
    LineOverlay,
)


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


LINES = {
    "canny_low": 10,
    "canny_high": 80,
    "rho_resolution": 1.0,
    "theta_resolution_degrees": 1.0,
    "vote_threshold": 1,
    "minimum_line_length": 0,
    "maximum_line_gap": 0,
    "maximum_lines": 2,
}
CIRCLES = {
    "median_kernel": 3,
    "dp": 1.2,
    "minimum_distance": 5,
    "canny_high_threshold": 100.0,
    "accumulator_threshold": 30.0,
    "minimum_radius": 0,
    "maximum_radius": 0,
    "maximum_circles": 2,
}
HARRIS = {
    "block_size": 2,
    "aperture_size": 3,
    "harris_k": 0.04,
    "quality_level": 0.01,
    "minimum_distance": 5.0,
    "maximum_corners": 4,
    "subpixel_refinement": False,
}


def test_hough_lines_canonicalized_sorted_capped_and_none(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    image = ImageAsset("gray", np.zeros((40, 40), dtype=np.uint8), ColourModel.GRAY)

    def fake_lines(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return np.array([[[30, 30, 0, 0]], [[5, 5, 20, 5]], [[0, 0, 39, 0]]], dtype=np.int32)

    monkeypatch.setattr("dip_workbench.operations.m10.hough_lines.cv2.HoughLinesP", fake_lines)
    result = HoughLinesExecutor().execute(context(image, LINES))
    overlays = result.primary_artifact.data.items
    assert isinstance(overlays[0], LineOverlay)
    assert len(overlays) == 2
    assert (overlays[0].x1, overlays[0].y1, overlays[0].x2, overlays[0].y2) == (0, 0, 30, 30)
    assert result.get_artifact("line_detections").data.rows[0][0] == 1
    monkeypatch.setattr(
        "dip_workbench.operations.m10.hough_lines.cv2.HoughLinesP", lambda *_a, **_k: None
    )
    empty = HoughLinesExecutor().execute(context(image, LINES))
    assert empty.primary_artifact.data.items == ()
    assert empty.get_artifact("line_detections").data.rows == ()


def test_hough_circles_sorted_capped_validation_and_none(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    image = ImageAsset("gray", np.zeros((50, 50), dtype=np.uint8), ColourModel.GRAY)
    raw = np.array([[[10.0, 10.0, 4.0], [20.0, 20.0, 9.0], [30.0, 30.0, -1.0]]])
    monkeypatch.setattr(
        "dip_workbench.operations.m10.hough_circles.cv2.HoughCircles", lambda *_a, **_k: raw
    )
    result = HoughCirclesExecutor().execute(context(image, CIRCLES))
    overlays = result.primary_artifact.data.items
    assert len(overlays) == 2
    assert isinstance(overlays[0], CircleOverlay)
    assert overlays[0].radius == 9.0
    assert result.get_artifact("circle_detections").data.rows[0] == (1, 20.0, 20.0, 9.0)
    with pytest.raises(InputValidationError):
        HoughCirclesExecutor().execute(
            context(image, {**CIRCLES, "minimum_radius": 10, "maximum_radius": 5})
        )
    monkeypatch.setattr(
        "dip_workbench.operations.m10.hough_circles.cv2.HoughCircles", lambda *_a, **_k: None
    )
    empty = HoughCirclesExecutor().execute(context(image, CIRCLES))
    assert empty.primary_artifact.data.items == ()
    assert empty.get_artifact("circle_detections").data.rows == ()


def test_harris_detects_respects_caps_and_constant_is_empty() -> None:
    data = np.zeros((40, 40), dtype=np.uint8)
    data[10:30, 10:30] = 255
    image = ImageAsset("square", data, ColourModel.GRAY)
    result = HarrisCornersExecutor().execute(context(image, HARRIS))
    assert 0 < len(result.primary_artifact.data.items) <= 4
    assert len(result.get_artifact("corner_detections").data.rows) == len(
        result.primary_artifact.data.items
    )
    capped = HarrisCornersExecutor().execute(context(image, {**HARRIS, "maximum_corners": 1}))
    assert len(capped.primary_artifact.data.items) == 1
    constant = ImageAsset("constant", np.full((20, 20), 80, dtype=np.uint8), ColourModel.GRAY)
    empty = HarrisCornersExecutor().execute(context(constant, HARRIS))
    assert empty.primary_artifact.data.items == ()
    assert empty.get_artifact("corner_detections").data.rows == ()
    np.testing.assert_array_equal(image.data, data)
