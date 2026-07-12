"""M04-02 Histogram Equalization."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import CurveArtifact, HistogramArtifact, ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.visualization import GraphData, GraphSeries, GraphStyle

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


def equalization_lut(values: np.ndarray) -> np.ndarray:
    counts, _ = np.histogram(values.reshape(-1), bins=256, range=(0, 256))
    cdf = np.cumsum(counts).astype(np.float64)
    nonzero = cdf[cdf > 0]
    if nonzero.size == 0 or nonzero[0] == cdf[-1]:
        return np.arange(256, dtype=np.uint8)
    scaled = (cdf - nonzero[0]) * (255.0 / (cdf[-1] - nonzero[0]))
    scaled[cdf == 0] = 0
    return np.ascontiguousarray(np.rint(np.clip(scaled, 0, 255)).astype(np.uint8))


def _gray(image: ImageAsset) -> np.ndarray:
    return (
        cv2.cvtColor(image.data, cv2.COLOR_RGB2GRAY)
        if image.colour_model is ColourModel.RGB
        else image.data
    )


def _hist_series(values: np.ndarray, label: str) -> GraphSeries:
    counts, edges = np.histogram(values.reshape(-1), bins=256, range=(0, 256))
    x = ((edges[:-1] + edges[1:]) / 2.0).astype(float)
    return GraphSeries(label, tuple(x.tolist()), tuple(counts.astype(float).tolist()))


class HistogramEqualizationExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Histogram Equalization requires RGB or grayscale input.")
        source_gray = _gray(image)
        lut = equalization_lut(source_gray)
        if image.colour_model is ColourModel.RGB:
            ycc = cv2.cvtColor(image.data, cv2.COLOR_RGB2YCrCb)
            ycc[..., 0] = cv2.LUT(ycc[..., 0], lut)
            output = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2RGB)
            handling = "luminance"
            output_gray = ycc[..., 0]
        else:
            output = cv2.LUT(image.data, lut)
            handling = "grayscale"
            output_gray = output
        context.cancellation_token.raise_if_cancelled()
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-equalized",
            data=np.ascontiguousarray(output, dtype=np.uint8),
            colour_model=image.colour_model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M04-02",
                "input_asset_id": image.id,
                "colour_handling": handling,
            },
        )
        hist_graph = GraphData(
            (_hist_series(source_gray, "Before"), _hist_series(output_gray, "After")),
            title="Before and After Histograms",
            x_label="Intensity",
            y_label="Frequency",
            style=GraphStyle.LINE,
        )
        values = np.arange(256, dtype=np.uint8)
        cdf_counts, _ = np.histogram(source_gray.reshape(-1), bins=256, range=(0, 256))
        cdf = np.cumsum(cdf_counts).astype(np.float64) / source_gray.size
        metrics = {
            "Input Mean": float(np.mean(source_gray)),
            "Output Mean": float(np.mean(output_gray)),
            "Input Standard Deviation": float(np.std(source_gray)),
            "Output Standard Deviation": float(np.std(output_gray)),
        }
        return OperationResult(
            ImageArtifact("equalized_image", "Equalized Image", asset),
            (
                HistogramArtifact(
                    "histogram_comparison", "Before and After Histograms", hist_graph
                ),
                CurveArtifact(
                    "input_cdf", "Input Cumulative Distribution", {"input": values, "output": cdf}
                ),
                CurveArtifact(
                    "equalization_mapping", "Equalization Mapping", {"input": values, "output": lut}
                ),
            ),
            metrics=metrics,
            metadata={"input_asset": image},
        )


def create_histogram_equalization_presenter() -> object:
    from dip_workbench.ui.operations.histograms import HistogramEqualizationPresenter

    return HistogramEqualizationPresenter()


HISTOGRAM_EQUALIZATION_DEFINITION = OperationDefinition(
    OperationId("M04-02"),
    ModuleId.M04,
    "Histogram Equalization",
    "Equalize image luminance contrast.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T3_ANALYSIS_AND_GRAPH,
    HistogramEqualizationExecutor,
    create_histogram_equalization_presenter,
)

operation_registry.register(HISTOGRAM_EQUALIZATION_DEFINITION)
