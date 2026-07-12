"""M10-05 Hough Circle Detection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, OverlayArtifact, TableArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m10.common import grayscale_u8, int_value, metadata_base, number
from dip_workbench.operations.overlays import CircleOverlay, OverlayData
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.visualization import TableData

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

MEDIAN_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7, 9))


def _radius_validator(_value: object, values: Mapping[str, object]) -> str | None:
    min_radius = values.get("minimum_radius")
    max_radius = values.get("maximum_radius")
    if (
        not isinstance(min_radius, int)
        or isinstance(min_radius, bool)
        or not isinstance(max_radius, int)
        or isinstance(max_radius, bool)
    ):
        return "Circle radii must be integers."
    if max_radius != 0 and max_radius < min_radius:
        return "Maximum radius must be automatic or greater than or equal to minimum radius."
    return None


def _circles(
    raw: np.ndarray | None, maximum: int
) -> tuple[tuple[CircleOverlay, tuple[object, ...]], ...]:
    if raw is None:
        return ()
    rows = []
    for x, y, radius in np.asarray(raw).reshape(-1, 3):
        if not np.isfinite((x, y, radius)).all() or radius <= 0:
            continue
        rows.append(
            (
                CircleOverlay(float(x), float(y), float(radius)),
                (0, float(x), float(y), float(radius)),
            )
        )
    rows.sort(key=lambda item: (-item[0].radius, item[0].center_x, item[0].center_y))
    capped = rows[:maximum]
    return tuple((circle, (index, *row[1:])) for index, (circle, row) in enumerate(capped, 1))


class HoughCirclesExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Hough circles require RGB or grayscale input.")
        error = _radius_validator(None, context.parameters)
        if error:
            raise InputValidationError(error)
        gray = grayscale_u8(image)
        kernel = int_value(context.parameters["median_kernel"], "Median kernel")
        dp = number(context.parameters["dp"], "DP")
        minimum_distance = int_value(context.parameters["minimum_distance"], "Minimum distance")
        canny_high = number(context.parameters["canny_high_threshold"], "Canny high threshold")
        accumulator = number(context.parameters["accumulator_threshold"], "Accumulator threshold")
        minimum_radius = int_value(context.parameters["minimum_radius"], "Minimum radius")
        maximum_radius = int_value(context.parameters["maximum_radius"], "Maximum radius")
        maximum_circles = int_value(context.parameters["maximum_circles"], "Maximum circles")
        context.cancellation_token.raise_if_cancelled()
        smoothed = cv2.medianBlur(gray, kernel)
        raw = cv2.HoughCircles(
            smoothed,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=minimum_distance,
            param1=canny_high,
            param2=accumulator,
            minRadius=minimum_radius,
            maxRadius=maximum_radius,
        )
        rows = _circles(raw, maximum_circles)
        context.cancellation_token.raise_if_cancelled()
        overlays = tuple(row[0] for row in rows)
        table_rows = tuple(row[1] for row in rows)
        radii = [circle.radius for circle in overlays]
        meta = metadata_base("M10-05", image, **dict(context.parameters))
        return OperationResult(
            OverlayArtifact("detected_circles", "Detected Circles", OverlayData(overlays)),
            (
                ImageArtifact(
                    "circle_preprocessed",
                    "Median-Blurred Input",
                    ImageAsset(
                        f"{Path(image.name).stem}-circle-preprocessed",
                        smoothed,
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                TableArtifact(
                    "circle_detections",
                    "Circle Detections",
                    TableData(("Index", "Center X", "Center Y", "Radius"), table_rows),
                ),
            ),
            metrics={
                "Detected Circles": len(rows),
                "Average Radius": float(np.mean(radii)) if radii else 0.0,
                "Largest Radius": float(max(radii, default=0.0)),
            },
            metadata={"input_asset": image},
        )


def create_hough_circles_presenter() -> object:
    from dip_workbench.ui.operations.geometric_features import GeometricFeaturePresenter

    return GeometricFeaturePresenter(
        "circle_preprocessed", "Median-Blurred Input", "circle_detections"
    )


HOUGH_CIRCLES_DEFINITION = OperationDefinition(
    OperationId("M10-05"),
    ModuleId.M10,
    "Hough Circle Detection",
    "Detect circles using the Hough gradient transform.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "median_kernel", "Median Kernel", ParameterType.ENUM, 5, choices=MEDIAN_CHOICES
        ),
        ParameterSpec("dp", "DP", ParameterType.FLOAT, 1.2, minimum=1.0, maximum=3.0, step=0.1),
        ParameterSpec(
            "minimum_distance",
            "Minimum Distance",
            ParameterType.INTEGER,
            20,
            minimum=1,
            maximum=2000,
        ),
        ParameterSpec(
            "canny_high_threshold",
            "Canny High Threshold",
            ParameterType.FLOAT,
            100.0,
            minimum=1.0,
            maximum=255.0,
            step=1.0,
        ),
        ParameterSpec(
            "accumulator_threshold",
            "Accumulator Threshold",
            ParameterType.FLOAT,
            30.0,
            minimum=1.0,
            maximum=255.0,
            step=1.0,
        ),
        ParameterSpec(
            "minimum_radius",
            "Minimum Radius",
            ParameterType.INTEGER,
            0,
            minimum=0,
            maximum=2000,
            validator=_radius_validator,
        ),
        ParameterSpec(
            "maximum_radius",
            "Maximum Radius",
            ParameterType.INTEGER,
            0,
            minimum=0,
            maximum=2000,
            validator=_radius_validator,
        ),
        ParameterSpec(
            "maximum_circles", "Maximum Circles", ParameterType.INTEGER, 50, minimum=1, maximum=200
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.NONE,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    HoughCirclesExecutor,
    create_hough_circles_presenter,
)

operation_registry.register(HOUGH_CIRCLES_DEFINITION)
