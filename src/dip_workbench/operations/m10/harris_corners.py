"""M10-06 Harris Corner Detection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, OverlayArtifact, TableArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m06.common import normalized_magnitude_image
from dip_workbench.operations.m10.common import grayscale_u8, int_value, metadata_base, number
from dip_workbench.operations.overlays import OverlayData, PointOverlay
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.visualization import TableData

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

APERTURE_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7))


def _detect_corners(
    response: np.ndarray,
    *,
    quality: float,
    minimum_distance: float,
    maximum: int,
) -> list[tuple[float, float, float]]:
    maximum_response = float(response.max())
    if maximum_response <= 0:
        return []
    threshold = quality * maximum_response
    local_max = cv2.dilate(
        response, np.ones((3, 3), dtype=np.uint8), borderType=cv2.BORDER_REFLECT_101
    )
    ys, xs = np.nonzero((response > threshold) & (response == local_max))
    candidates = sorted(
        ((float(response[y, x]), float(x), float(y)) for y, x in zip(ys, xs, strict=True)),
        key=lambda item: (-item[0], item[2], item[1]),
    )
    accepted: list[tuple[float, float, float]] = []
    for value, x, y in candidates:
        if all(
            np.hypot(x - old_x, y - old_y) >= minimum_distance
            for old_x, old_y, _old_value in accepted
        ):
            accepted.append((x, y, value))
            if len(accepted) >= maximum:
                break
    return accepted


class HarrisCornersExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Harris corners require RGB or grayscale input.")
        block = int_value(context.parameters["block_size"], "Block size")
        aperture = int_value(context.parameters["aperture_size"], "Aperture size")
        harris_k = number(context.parameters["harris_k"], "Harris k")
        quality = number(context.parameters["quality_level"], "Quality level")
        minimum_distance = number(context.parameters["minimum_distance"], "Minimum distance")
        maximum_corners = int_value(context.parameters["maximum_corners"], "Maximum corners")
        if min(image.width, image.height) < max(block, aperture):
            raise InputValidationError("Image is too small for the selected Harris neighbourhood.")
        gray = grayscale_u8(image)
        context.cancellation_token.raise_if_cancelled()
        response = cv2.cornerHarris(
            gray.astype(np.float32),
            blockSize=block,
            ksize=aperture,
            k=harris_k,
            borderType=cv2.BORDER_REFLECT_101,
        )
        corners = _detect_corners(
            response,
            quality=quality,
            minimum_distance=minimum_distance,
            maximum=maximum_corners,
        )
        if corners and bool(context.parameters["subpixel_refinement"]):
            points = np.asarray([[x, y] for x, y, _value in corners], dtype=np.float32).reshape(
                -1, 1, 2
            )
            win = (min(5, max(1, image.width // 2)), min(5, max(1, image.height // 2)))
            refined = cv2.cornerSubPix(
                gray,
                points,
                win,
                (-1, -1),
                (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01),
            )
            corners = [
                (
                    float(np.clip(point[0][0], 0, image.width - 1)),
                    float(np.clip(point[0][1], 0, image.height - 1)),
                    value,
                )
                for point, (_x, _y, value) in zip(refined, corners, strict=True)
            ]
        context.cancellation_token.raise_if_cancelled()
        overlays = tuple(PointOverlay(x, y, 3.0) for x, y, _value in corners)
        table_rows = tuple((index, x, y, value) for index, (x, y, value) in enumerate(corners, 1))
        threshold = quality * float(response.max()) if response.max() > 0 else 0.0
        positive = np.clip(response, 0, None)
        meta = metadata_base("M10-06", image, **dict(context.parameters))
        return OperationResult(
            OverlayArtifact("detected_corners", "Detected Corners", OverlayData(overlays)),
            (
                ImageArtifact(
                    "harris_response_display",
                    "Harris Response",
                    ImageAsset(
                        f"{Path(image.name).stem}-harris-response",
                        normalized_magnitude_image(positive),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "harris_response_signed",
                    "Signed Harris Response",
                    FloatingImage(
                        "harris-response",
                        response.astype(np.float32),
                        {**meta, "response_type": "harris"},
                    ),
                    exportable=False,
                ),
                TableArtifact(
                    "corner_detections",
                    "Corner Detections",
                    TableData(("Index", "X", "Y", "Response"), table_rows),
                ),
            ),
            metrics={
                "Detected Corners": len(corners),
                "Maximum Harris Response": float(response.max()),
                "Response Threshold": threshold,
            },
            metadata={"input_asset": image},
        )


def create_harris_presenter() -> object:
    from dip_workbench.ui.operations.geometric_features import GeometricFeaturePresenter

    return GeometricFeaturePresenter(
        "harris_response_display", "Harris Response", "corner_detections"
    )


HARRIS_CORNERS_DEFINITION = OperationDefinition(
    OperationId("M10-06"),
    ModuleId.M10,
    "Harris Corner Detection",
    "Detect corner points using a Harris response map.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec("block_size", "Block Size", ParameterType.INTEGER, 2, minimum=2, maximum=15),
        ParameterSpec(
            "aperture_size", "Aperture Size", ParameterType.ENUM, 3, choices=APERTURE_CHOICES
        ),
        ParameterSpec(
            "harris_k", "Harris k", ParameterType.FLOAT, 0.04, minimum=0.01, maximum=0.20, step=0.01
        ),
        ParameterSpec(
            "quality_level",
            "Quality Level",
            ParameterType.FLOAT,
            0.01,
            minimum=0.001,
            maximum=0.20,
            step=0.001,
        ),
        ParameterSpec(
            "minimum_distance",
            "Minimum Distance",
            ParameterType.FLOAT,
            10.0,
            minimum=1.0,
            maximum=100.0,
            step=1.0,
        ),
        ParameterSpec(
            "maximum_corners",
            "Maximum Corners",
            ParameterType.INTEGER,
            200,
            minimum=1,
            maximum=1000,
        ),
        ParameterSpec("subpixel_refinement", "Subpixel Refinement", ParameterType.BOOLEAN, False),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.NONE,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    HarrisCornersExecutor,
    create_harris_presenter,
)

operation_registry.register(HARRIS_CORNERS_DEFINITION)
