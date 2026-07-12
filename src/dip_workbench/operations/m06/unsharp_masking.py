"""M06-05 Unsharp Masking."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
    clipped_uint8_plane,
    gaussian_detail_components,
    luminance_working_plane,
    rebuild_from_luminance,
    signed_response_image,
)
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

KERNEL_CHOICES = tuple(ParameterChoice(v, str(v)) for v in (3, 5, 7, 9, 11))


class UnsharpMaskingExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Unsharp masking requires RGB or grayscale input.")
        ksize = context.parameters.get("kernel_size")
        sigma = context.parameters.get("sigma")
        amount = context.parameters.get("amount")
        if not isinstance(ksize, int) or ksize not in {3, 5, 7, 9, 11}:
            raise InputValidationError("Unsharp kernel size is invalid.")
        if not isinstance(sigma, (int, float)) or isinstance(sigma, bool):
            raise InputValidationError("Unsharp sigma must be numeric.")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InputValidationError("Unsharp amount must be numeric.")
        plane, ycc, model = luminance_working_plane(image)
        context.cancellation_token.raise_if_cancelled()
        blur, detail = gaussian_detail_components(plane, kernel_size=ksize, sigma=float(sigma))
        enhanced_plane = plane + float(amount) * detail
        clipped_plane = clipped_uint8_plane(enhanced_plane)
        output = rebuild_from_luminance(enhanced_plane, ycc, model)
        blurred = rebuild_from_luminance(blur, ycc, model)
        detail_display = signed_response_image(detail)
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M06-05",
            "input_asset_id": image.id,
            "kernel_size": ksize,
            "sigma": float(sigma),
            "amount": float(amount),
        }
        return OperationResult(
            ImageArtifact(
                "unsharp_image",
                "Unsharp Image",
                ImageAsset(
                    f"{Path(image.name).stem}-unsharp",
                    output,
                    model,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "blurred_image",
                    "Blurred Image",
                    ImageAsset(
                        f"{Path(image.name).stem}-blurred",
                        blurred,
                        model,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "detail_display",
                    "Detail Mask",
                    ImageAsset(
                        f"{Path(image.name).stem}-detail",
                        detail_display,
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "detail_signed",
                    "Signed Detail",
                    FloatingImage("unsharp-detail", detail, {**meta, "response_type": "detail"}),
                    exportable=False,
                ),
            ),
            metrics={
                "Detail Minimum": float(detail.min()),
                "Detail Maximum": float(detail.max()),
                "Detail Standard Deviation": float(np.std(detail)),
                "Input Standard Deviation": float(np.std(plane)),
                "Output Standard Deviation": float(np.std(clipped_plane)),
            },
            metadata={"input_asset": image},
        )


def create_unsharp_masking_presenter() -> object:
    from dip_workbench.ui.operations.sharpening import DetailSharpeningPresenter

    return DetailSharpeningPresenter("unsharp_image")


UNSHARP_MASKING_DEFINITION = OperationDefinition(
    OperationId("M06-05"),
    ModuleId.M06,
    "Unsharp Masking",
    "Sharpen an image by adding a scaled high-frequency detail mask.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec("kernel_size", "Kernel Size", ParameterType.ENUM, 5, choices=KERNEL_CHOICES),
        ParameterSpec(
            "sigma", "Sigma", ParameterType.FLOAT, 0.0, minimum=0.0, maximum=10.0, step=0.1
        ),
        ParameterSpec(
            "amount", "Amount", ParameterType.FLOAT, 0.5, minimum=0.1, maximum=1.0, step=0.05
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T4_OVERLAY_AND_FEATURE_DETECTION,
    UnsharpMaskingExecutor,
    create_unsharp_masking_presenter,
    ("unsharp", "unsharp masking", "detail mask sharpening"),
)

operation_registry.register(UNSHARP_MASKING_DEFINITION)
