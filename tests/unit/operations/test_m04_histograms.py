"""Focused tests for M04 histogram operations."""

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    HistogramAnalysisExecutor,
    HistogramEqualizationExecutor,
    equalization_lut,
)


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


def test_histogram_counts_normalized_and_cumulative() -> None:
    image = ImageAsset("gray", np.array([[0, 0, 255, 255]], dtype=np.uint8), ColourModel.GRAY)
    ordinary = HistogramAnalysisExecutor().execute(context(image, {"mode": "ordinary", "bins": 16}))
    normalized = HistogramAnalysisExecutor().execute(
        context(image, {"mode": "normalized", "bins": 16})
    )
    cumulative = HistogramAnalysisExecutor().execute(
        context(image, {"mode": "cumulative", "bins": 16})
    )
    assert sum(ordinary.primary_artifact.data.series[0].y) == image.data.size  # type: ignore[union-attr]
    assert sum(normalized.primary_artifact.data.series[0].y) == 1.0  # type: ignore[union-attr]
    assert cumulative.primary_artifact.data.series[0].y[-1] == 1.0  # type: ignore[union-attr]


def test_rgb_series_use_canonical_rgb_order() -> None:
    image = ImageAsset("rgb", np.array([[[10, 20, 30]]], dtype=np.uint8), ColourModel.RGB)
    result = HistogramAnalysisExecutor().execute(context(image, {"mode": "ordinary", "bins": 256}))
    graph = result.primary_artifact.data
    peaks = {series.label: series.x[series.y.index(max(series.y))] for series in graph.series}  # type: ignore[union-attr]
    assert peaks == {"Red": 10.5, "Green": 20.5, "Blue": 30.5}


def test_equalization_lut_matches_mapping_and_constant_safe() -> None:
    constant = ImageAsset("flat", np.full((3, 3), 80, dtype=np.uint8), ColourModel.GRAY)
    result = HistogramEqualizationExecutor().execute(context(constant, {}))
    np.testing.assert_array_equal(result.primary_artifact.data.data, constant.data)  # type: ignore[union-attr]
    mapping = result.get_artifact("equalization_mapping").data["output"]  # type: ignore[index]
    np.testing.assert_array_equal(mapping, equalization_lut(constant.data))


def test_rgb_equalization_preserves_shape_and_luminance_strategy() -> None:
    data = np.array(
        [[[30, 40, 50], [120, 130, 140]], [[200, 210, 220], [230, 240, 250]]], dtype=np.uint8
    )
    image = ImageAsset("rgb", data, ColourModel.RGB)
    result = HistogramEqualizationExecutor().execute(context(image, {}))
    output = result.primary_artifact.data
    assert output.colour_model is ColourModel.RGB  # type: ignore[union-attr]
    assert output.shape == image.shape  # type: ignore[union-attr]
    expected = cv2.cvtColor(data, cv2.COLOR_RGB2YCrCb)
    expected[..., 0] = cv2.LUT(expected[..., 0], equalization_lut(expected[..., 0]))
    expected = cv2.cvtColor(expected, cv2.COLOR_YCrCb2RGB)
    np.testing.assert_array_equal(output.data, expected)  # type: ignore[union-attr]
