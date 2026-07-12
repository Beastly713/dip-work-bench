"""M03-03 Gamma Correction."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import CurveArtifact, ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution.contracts import OperationContext


class GammaCorrectionExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Gamma Correction requires RGB or grayscale input.")
        gamma = context.parameters.get("gamma")
        if not isinstance(gamma, (int, float)) or isinstance(gamma, bool):
            raise InputValidationError("Gamma must be numeric.")
        values = np.arange(256, dtype=np.float32)
        table = (
            np.rint(255.0 * np.power(values / 255.0, float(gamma))).clip(0, 255).astype(np.uint8)
        )
        output = cv2.LUT(image.data, table)
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-gamma",
            data=np.ascontiguousarray(output, dtype=np.uint8),
            colour_model=image.colour_model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M03-03",
                "input_asset_id": image.id,
                "gamma": float(gamma),
            },
        )
        return OperationResult(
            ImageArtifact("gamma_corrected_image", "Gamma-Corrected Image", asset),
            (
                CurveArtifact(
                    "gamma_curve",
                    "Gamma Transformation Curve",
                    {"input": np.arange(256, dtype=np.uint8), "output": table},
                ),
            ),
            metadata={"input_asset": image},
        )


def create_gamma_correction_presenter() -> object:
    from dip_workbench.ui.operations.common import BeforeAfterImageWithCurvePresenter

    return BeforeAfterImageWithCurvePresenter(
        result_label="Gamma-Corrected Result",
        curve_label="Gamma Transformation Curve",
    )


GAMMA_CORRECTION_DEFINITION = OperationDefinition(
    OperationId("M03-03"),
    ModuleId.M03,
    "Gamma Correction",
    "Apply power-law gamma correction.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "gamma", "Gamma", ParameterType.FLOAT, 1.0, minimum=0.1, maximum=5.0, step=0.05
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    GammaCorrectionExecutor,
    create_gamma_correction_presenter,
)

operation_registry.register(GAMMA_CORRECTION_DEFINITION)
