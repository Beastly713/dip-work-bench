"""M06-01 First-Order Gradient."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m06.common import (
    grayscale_float,
    normalized_magnitude_image,
    signed_response_image,
)
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

METHODS = tuple(
    ParameterChoice(v, label)
    for v, label in (
        ("forward", "Forward"),
        ("central", "Central"),
        ("roberts", "Roberts"),
        ("prewitt", "Prewitt"),
    )
)


def _kernels(method: object) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    if method == "forward":
        return (
            np.array([[0, 0, 0], [0, -1, 1], [0, 0, 0]], dtype=np.float32),
            np.array([[0, 0, 0], [0, -1, 0], [0, 1, 0]], dtype=np.float32),
            (-1, -1),
        )
    if method == "central":
        return (
            np.array([[0, 0, 0], [-0.5, 0, 0.5], [0, 0, 0]], dtype=np.float32),
            np.array([[0, -0.5, 0], [0, 0, 0], [0, 0.5, 0]], dtype=np.float32),
            (-1, -1),
        )
    if method == "roberts":
        return (
            np.array([[1, 0], [0, -1]], dtype=np.float32),
            np.array([[0, 1], [-1, 0]], dtype=np.float32),
            (0, 0),
        )
    if method == "prewitt":
        return (
            np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float32),
            np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float32),
            (-1, -1),
        )
    raise InputValidationError("Gradient method is invalid.")


class FirstOrderGradientExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("First-order gradient requires RGB or grayscale input.")
        method = context.parameters.get("method")
        gray = grayscale_float(image)
        context.cancellation_token.raise_if_cancelled()
        kx, ky, anchor = _kernels(method)
        gx = cv2.filter2D(gray, cv2.CV_32F, kx, anchor=anchor, borderType=cv2.BORDER_REFLECT_101)
        gy = cv2.filter2D(gray, cv2.CV_32F, ky, anchor=anchor, borderType=cv2.BORDER_REFLECT_101)
        magnitude = np.hypot(gx, gy)
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M06-01",
            "input_asset_id": image.id,
            "method": method,
            "border": "reflect",
        }
        mag = ImageAsset(
            f"{Path(image.name).stem}-gradient",
            normalized_magnitude_image(magnitude),
            ColourModel.GRAY,
            source_path=image.source_path,
            metadata=meta,
        )
        x_display = ImageAsset(
            f"{Path(image.name).stem}-gradient-x",
            signed_response_image(gx),
            ColourModel.GRAY,
            source_path=image.source_path,
            metadata=meta,
        )
        y_display = ImageAsset(
            f"{Path(image.name).stem}-gradient-y",
            signed_response_image(gy),
            ColourModel.GRAY,
            source_path=image.source_path,
            metadata=meta,
        )
        return OperationResult(
            ImageArtifact("gradient_magnitude", "Gradient Magnitude", mag),
            (
                ImageArtifact("gradient_x_display", "Horizontal Response", x_display),
                ImageArtifact("gradient_y_display", "Vertical Response", y_display),
                ImageArtifact(
                    "gradient_x_signed",
                    "Horizontal Signed Response",
                    FloatingImage("gradient-x", gx, {**meta, "response_type": "gradient_x"}),
                    exportable=False,
                ),
                ImageArtifact(
                    "gradient_y_signed",
                    "Vertical Signed Response",
                    FloatingImage("gradient-y", gy, {**meta, "response_type": "gradient_y"}),
                    exportable=False,
                ),
            ),
            metrics={
                "Gx Minimum": float(gx.min()),
                "Gx Maximum": float(gx.max()),
                "Gy Minimum": float(gy.min()),
                "Gy Maximum": float(gy.max()),
                "Magnitude Maximum": float(magnitude.max()),
            },
            metadata={"input_asset": image},
        )


def create_first_order_gradient_presenter() -> object:
    from dip_workbench.ui.operations.derivatives import DerivativeTriplePresenter

    return DerivativeTriplePresenter(
        "gradient_x_display", "gradient_y_display", "gradient_magnitude"
    )


FIRST_ORDER_GRADIENT_DEFINITION = OperationDefinition(
    OperationId("M06-01"),
    ModuleId.M06,
    "First-Order Gradient",
    "Calculate first derivative gradient responses.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (ParameterSpec("method", "Method", ParameterType.ENUM, "central", choices=METHODS),),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    FirstOrderGradientExecutor,
    create_first_order_gradient_presenter,
    (
        "gradient",
        "first derivative",
        "forward difference",
        "central difference",
        "roberts",
        "prewitt",
        "edge gradient",
    ),
)

operation_registry.register(FIRST_ORDER_GRADIENT_DEFINITION)
