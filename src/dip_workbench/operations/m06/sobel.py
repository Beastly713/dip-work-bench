"""M06-02 Sobel Edge Enhancement."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact, MaskArtifact
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
from dip_workbench.operations.parameters import (
    ConditionOperator,
    ParameterChoice,
    ParameterCondition,
    ParameterSpec,
    ParameterType,
)
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

KERNEL_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7))


class SobelExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Sobel requires RGB or grayscale input.")
        ksize = context.parameters.get("kernel_size")
        scale = context.parameters.get("scale")
        threshold_enabled = bool(context.parameters.get("threshold_enabled"))
        threshold = context.parameters.get("threshold")
        if not isinstance(ksize, int) or ksize not in {3, 5, 7}:
            raise InputValidationError("Sobel kernel size is invalid.")
        if not isinstance(scale, (int, float)) or isinstance(scale, bool):
            raise InputValidationError("Sobel scale must be numeric.")
        if not isinstance(threshold, int) or isinstance(threshold, bool):
            raise InputValidationError("Sobel threshold must be an integer.")
        gray = grayscale_float(image)
        context.cancellation_token.raise_if_cancelled()
        gx = cv2.Sobel(
            gray,
            cv2.CV_32F,
            1,
            0,
            ksize=ksize,
            scale=float(scale),
            borderType=cv2.BORDER_REFLECT_101,
        )
        gy = cv2.Sobel(
            gray,
            cv2.CV_32F,
            0,
            1,
            ksize=ksize,
            scale=float(scale),
            borderType=cv2.BORDER_REFLECT_101,
        )
        magnitude = np.hypot(gx, gy)
        normalized = normalized_magnitude_image(magnitude)
        output = (
            np.where(normalized >= threshold, 255, 0).astype(np.uint8)
            if threshold_enabled
            else normalized
        )
        model = ColourModel.BINARY if threshold_enabled else ColourModel.GRAY
        artifact_cls = MaskArtifact if threshold_enabled else ImageArtifact
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M06-02",
            "input_asset_id": image.id,
            "kernel_size": ksize,
            "scale": float(scale),
            "threshold_enabled": threshold_enabled,
            "threshold": threshold,
        }
        primary = ImageAsset(
            f"{Path(image.name).stem}-sobel",
            np.ascontiguousarray(output),
            model,
            source_path=image.source_path,
            metadata=meta,
        )
        x_display = ImageAsset(
            f"{Path(image.name).stem}-sobel-x",
            signed_response_image(gx),
            ColourModel.GRAY,
            source_path=image.source_path,
            metadata=meta,
        )
        y_display = ImageAsset(
            f"{Path(image.name).stem}-sobel-y",
            signed_response_image(gy),
            ColourModel.GRAY,
            source_path=image.source_path,
            metadata=meta,
        )
        return OperationResult(
            artifact_cls("sobel_result", "Sobel Edge Result", primary),
            (
                ImageArtifact("sobel_x_display", "Horizontal Response", x_display),
                ImageArtifact("sobel_y_display", "Vertical Response", y_display),
                ImageArtifact(
                    "sobel_x_signed",
                    "Sobel X Signed",
                    FloatingImage("sobel-x", gx, {**meta, "response_type": "sobel_x"}),
                    exportable=False,
                ),
                ImageArtifact(
                    "sobel_y_signed",
                    "Sobel Y Signed",
                    FloatingImage("sobel-y", gy, {**meta, "response_type": "sobel_y"}),
                    exportable=False,
                ),
            ),
            metrics={
                "Gx Minimum": float(gx.min()),
                "Gx Maximum": float(gx.max()),
                "Gy Minimum": float(gy.min()),
                "Gy Maximum": float(gy.max()),
                "Magnitude Maximum": float(magnitude.max()),
                "Edge Pixels": int(np.count_nonzero(output == 255)) if threshold_enabled else 0,
            },
            metadata={"input_asset": image},
        )


def create_sobel_presenter() -> object:
    from dip_workbench.ui.operations.derivatives import DerivativeTriplePresenter

    return DerivativeTriplePresenter("sobel_x_display", "sobel_y_display", "sobel_result")


SOBEL_DEFINITION = OperationDefinition(
    OperationId("M06-02"),
    ModuleId.M06,
    "Sobel Edge Enhancement",
    "Calculate Sobel gradient magnitude and optional threshold.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec("kernel_size", "Kernel Size", ParameterType.ENUM, 3, choices=KERNEL_CHOICES),
        ParameterSpec(
            "scale", "Scale", ParameterType.FLOAT, 1.0, minimum=0.1, maximum=5.0, step=0.1
        ),
        ParameterSpec("threshold_enabled", "Enable Threshold", ParameterType.BOOLEAN, False),
        ParameterSpec(
            "threshold",
            "Display Threshold (0-255)",
            ParameterType.INTEGER,
            100,
            minimum=0,
            maximum=255,
            enabled_when=ParameterCondition("threshold_enabled", ConditionOperator.TRUTHY),
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    SobelExecutor,
    create_sobel_presenter,
)

operation_registry.register(SOBEL_DEFINITION)
