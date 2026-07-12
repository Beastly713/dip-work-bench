"""M04-01 Histogram Viewer and Analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import HistogramArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.visualization import GraphData, GraphSeries, GraphStyle

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

HISTOGRAM_MODES = (
    ParameterChoice("ordinary", "Ordinary"),
    ParameterChoice("normalized", "Normalized"),
    ParameterChoice("cumulative", "Cumulative"),
)
BIN_CHOICES = tuple(ParameterChoice(value, str(value)) for value in (16, 32, 64, 128, 256))


def intensity_histogram(values: np.ndarray, *, bins: int, mode: object, label: str) -> GraphSeries:
    counts, edges = np.histogram(values.reshape(-1), bins=bins, range=(0, 256))
    x = ((edges[:-1] + edges[1:]) / 2.0).astype(float)
    y = counts.astype(np.float64)
    total = float(values.size)
    if mode == "normalized":
        y = y / total
    elif mode == "cumulative":
        y = np.cumsum(y) / total
    elif mode != "ordinary":
        raise InputValidationError("Histogram mode is invalid.")
    return GraphSeries(label, tuple(x.tolist()), tuple(y.tolist()))


def histogram_graph(
    series: tuple[GraphSeries, ...], *, mode: object, rgb: bool = False
) -> GraphData:
    style = GraphStyle.LINE if mode == "cumulative" or rgb else GraphStyle.BAR
    y_label = "Probability" if mode in {"normalized", "cumulative"} else "Frequency"
    return GraphData(
        series,
        title="Histogram",
        x_label="Intensity",
        y_label=y_label,
        style=style,
    )


class HistogramAnalysisExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
            ColourModel.BINARY,
        }:
            raise InputValidationError("Histogram analysis requires an image.")
        mode = context.parameters.get("mode")
        bins = context.parameters.get("bins")
        if not isinstance(bins, int) or bins not in {16, 32, 64, 128, 256}:
            raise InputValidationError("Histogram bins are invalid.")
        gray = (
            cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
            if image.colour_model is ColourModel.RGB
            else image.data
        )
        gray_series = (intensity_histogram(gray, bins=bins, mode=mode, label="Grayscale"),)
        gray_graph = histogram_graph(gray_series, mode=mode, rgb=False)
        context.cancellation_token.raise_if_cancelled()
        artifacts: tuple[HistogramArtifact, ...]
        primary = HistogramArtifact("grayscale_histogram", "Grayscale Histogram", gray_graph)
        if image.colour_model is ColourModel.RGB:
            rgb_series = tuple(
                intensity_histogram(image.data[..., index], bins=bins, mode=mode, label=label)
                for index, label in enumerate(("Red", "Green", "Blue"))
            )
            rgb_graph = histogram_graph(rgb_series, mode=mode, rgb=True)
            rgb_artifact = HistogramArtifact("rgb_histogram", "RGB Histogram", rgb_graph)
            primary = rgb_artifact
            artifacts = (
                HistogramArtifact("grayscale_histogram", "Grayscale Histogram", gray_graph),
            )
        else:
            artifacts = ()
        values = gray.astype(np.float64)
        metrics = {
            "Mean": float(np.mean(values)),
            "Variance": float(np.var(values)),
            "Standard Deviation": float(np.std(values)),
            "Pixel Count": int(values.size),
            "Minimum Intensity": int(np.min(values)),
            "Maximum Intensity": int(np.max(values)),
        }
        return OperationResult(primary, artifacts, metrics=metrics, metadata={"input_asset": image})


def create_histogram_analysis_presenter() -> object:
    from dip_workbench.ui.operations.histograms import HistogramAnalysisPresenter

    return HistogramAnalysisPresenter()


HISTOGRAM_ANALYSIS_DEFINITION = OperationDefinition(
    OperationId("M04-01"),
    ModuleId.M04,
    "Histogram Viewer and Analysis",
    "Inspect intensity histograms and image statistics.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset(
                {ColourModel.RGB, ColourModel.GRAY, ColourModel.BINARY}
            ),
        ),
    ),
    (
        ParameterSpec("mode", "Mode", ParameterType.ENUM, "ordinary", choices=HISTOGRAM_MODES),
        ParameterSpec("bins", "Bins", ParameterType.ENUM, 256, choices=BIN_CHOICES),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.NONE,
    PresenterId.T3_ANALYSIS_AND_GRAPH,
    HistogramAnalysisExecutor,
    create_histogram_analysis_presenter,
    (
        "histogram",
        "intensity distribution",
        "rgb histogram",
        "cdf",
        "frequency distribution",
        "image statistics",
    ),
)

operation_registry.register(HISTOGRAM_ANALYSIS_DEFINITION)
