"""M10-04 Hough Line Detection."""

from __future__ import annotations

from math import atan2, degrees, hypot
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import MaskArtifact, OverlayArtifact, TableArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m10.common import (
    canny_edge_map,
    grayscale_u8,
    int_value,
    metadata_base,
    number,
    threshold_pair_validator,
    validate_threshold_pair,
)
from dip_workbench.operations.overlays import LineOverlay, OverlayData
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.visualization import TableData

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


def _line_rows(
    lines: np.ndarray | None, *, width: int, height: int, maximum: int
) -> tuple[tuple[LineOverlay, tuple[object, ...], float], ...]:
    if lines is None:
        return ()
    rows = []
    for raw in np.asarray(lines).reshape(-1, 4):
        if not np.isfinite(raw).all():
            continue
        x1, y1, x2, y2 = [round(float(v)) for v in raw]
        x1, x2 = max(0, min(width - 1, x1)), max(0, min(width - 1, x2))
        y1, y2 = max(0, min(height - 1, y1)), max(0, min(height - 1, y2))
        if (x2, y2) < (x1, y1):
            x1, y1, x2, y2 = x2, y2, x1, y1
        length = float(hypot(x2 - x1, y2 - y1))
        angle = (degrees(atan2(y2 - y1, x2 - x1)) + 180.0) % 180.0
        rows.append((LineOverlay(x1, y1, x2, y2), (0, x1, y1, x2, y2, length, angle), length))
    rows.sort(key=lambda item: (-item[2], item[0].x1, item[0].y1, item[0].x2, item[0].y2))
    capped = rows[:maximum]
    return tuple(
        (overlay, (index, *row[1:]), length)
        for index, (overlay, row, length) in enumerate(capped, 1)
    )


class HoughLinesExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Hough lines require RGB or grayscale input.")
        low, high = validate_threshold_pair(
            context.parameters.get("canny_low"),
            context.parameters.get("canny_high"),
            "Hough line Canny",
        )
        rho = number(context.parameters["rho_resolution"], "Rho resolution")
        theta = number(context.parameters["theta_resolution_degrees"], "Theta resolution")
        vote = int_value(context.parameters["vote_threshold"], "Vote threshold")
        min_len = int_value(context.parameters["minimum_line_length"], "Minimum line length")
        max_gap = int_value(context.parameters["maximum_line_gap"], "Maximum line gap")
        maximum = int_value(context.parameters["maximum_lines"], "Maximum lines")
        gray = grayscale_u8(image)
        smoothed, edge_map = canny_edge_map(
            gray,
            blur_kernel=5,
            sigma=1.0,
            low_threshold=low,
            high_threshold=high,
            aperture_size=3,
            l2_gradient=True,
        )
        del smoothed
        context.cancellation_token.raise_if_cancelled()
        raw = cv2.HoughLinesP(
            edge_map,
            rho=rho,
            theta=np.deg2rad(theta),
            threshold=vote,
            minLineLength=min_len,
            maxLineGap=max_gap,
        )
        rows = _line_rows(raw, width=image.width, height=image.height, maximum=maximum)
        context.cancellation_token.raise_if_cancelled()
        overlays = tuple(row[0] for row in rows)
        table_rows = tuple(row[1] for row in rows)
        lengths = [row[2] for row in rows]
        meta = metadata_base(
            "M10-04",
            image,
            canny_low=int(low),
            canny_high=int(high),
            rho_resolution=rho,
            theta_resolution_degrees=theta,
            vote_threshold=vote,
            minimum_line_length=min_len,
            maximum_line_gap=max_gap,
            maximum_lines=maximum,
            preprocessing="gaussian5_sigma1_canny_l2_aperture3",
        )
        return OperationResult(
            OverlayArtifact("detected_lines", "Detected Lines", OverlayData(overlays)),
            (
                MaskArtifact(
                    "line_edge_map",
                    "Canny Edge Map",
                    ImageAsset(
                        f"{Path(image.name).stem}-line-edges",
                        edge_map,
                        ColourModel.BINARY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                TableArtifact(
                    "line_detections",
                    "Line Detections",
                    TableData(
                        ("Index", "X1", "Y1", "X2", "Y2", "Length", "Angle Degrees"), table_rows
                    ),
                ),
            ),
            metrics={
                "Detected Lines": len(rows),
                "Total Line Length": float(sum(lengths)),
                "Longest Line Length": float(max(lengths, default=0.0)),
            },
            metadata={"input_asset": image},
        )


def create_hough_lines_presenter() -> object:
    from dip_workbench.ui.operations.geometric_features import GeometricFeaturePresenter

    return GeometricFeaturePresenter("line_edge_map", "Canny Edge Map", "line_detections")


HOUGH_LINES_DEFINITION = OperationDefinition(
    OperationId("M10-04"),
    ModuleId.M10,
    "Hough Line Detection",
    "Detect line segments using a probabilistic Hough transform.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "canny_low",
            "Canny Low",
            ParameterType.INTEGER,
            50,
            minimum=0,
            maximum=255,
            validator=threshold_pair_validator("canny_low", "canny_high", "Hough line Canny"),
        ),
        ParameterSpec(
            "canny_high",
            "Canny High",
            ParameterType.INTEGER,
            150,
            minimum=0,
            maximum=255,
            validator=threshold_pair_validator("canny_low", "canny_high", "Hough line Canny"),
        ),
        ParameterSpec(
            "rho_resolution",
            "Rho Resolution",
            ParameterType.FLOAT,
            1.0,
            minimum=0.5,
            maximum=5.0,
            step=0.5,
        ),
        ParameterSpec(
            "theta_resolution_degrees",
            "Theta Resolution Degrees",
            ParameterType.FLOAT,
            1.0,
            minimum=0.5,
            maximum=10.0,
            step=0.5,
        ),
        ParameterSpec(
            "vote_threshold", "Vote Threshold", ParameterType.INTEGER, 50, minimum=1, maximum=1000
        ),
        ParameterSpec(
            "minimum_line_length",
            "Minimum Line Length",
            ParameterType.INTEGER,
            30,
            minimum=0,
            maximum=5000,
        ),
        ParameterSpec(
            "maximum_line_gap",
            "Maximum Line Gap",
            ParameterType.INTEGER,
            10,
            minimum=0,
            maximum=1000,
        ),
        ParameterSpec(
            "maximum_lines", "Maximum Lines", ParameterType.INTEGER, 100, minimum=1, maximum=500
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.NONE,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    HoughLinesExecutor,
    create_hough_lines_presenter,
)

operation_registry.register(HOUGH_LINES_DEFINITION)
