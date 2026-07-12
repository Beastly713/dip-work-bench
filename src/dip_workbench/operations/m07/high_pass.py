"""M07-04 Frequency-Domain High-Pass Filter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
from dip_workbench.operations.m07.common import (
    circular_frequency_mask,
    grayscale_float,
    inverse_shifted_fft,
    magnitude_display,
    normalize_float_display,
    shifted_fft,
)
from dip_workbench.operations.m10.common import number
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


class HighPassExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("High-pass filtering requires RGB or grayscale input.")
        cutoff = number(context.parameters["cutoff_percent"], "Cutoff percent")
        gray = grayscale_float(image)
        context.cancellation_token.raise_if_cancelled()
        spectrum = shifted_fft(gray)
        context.cancellation_token.raise_if_cancelled()
        mask, radius = circular_frequency_mask(gray.shape, cutoff, pass_type="high")
        filtered = spectrum * mask
        response = inverse_shifted_fft(filtered)
        response[np.isclose(response, 0.0, atol=1e-4)] = 0.0
        context.cancellation_token.raise_if_cancelled()
        result = normalize_float_display(np.abs(response))
        mask_image = np.where(mask, 255, 0).astype(np.uint8)
        retained = int(np.count_nonzero(mask))
        meta = {
            "operation_id": "M07-04",
            "input_asset_id": image.id,
            "filter_type": "ideal_high_pass",
            "cutoff_percent": cutoff,
            "cutoff_radius": radius,
            "display_mapping": "normalized_absolute",
            "colour_conversion": "RGB2GRAY" if image.colour_model is ColourModel.RGB else "none",
        }
        return OperationResult(
            ImageArtifact(
                "high_pass_result",
                "Normalized High-Pass Response",
                ImageAsset(
                    f"{Path(image.name).stem}-high-pass",
                    result,
                    ColourModel.GRAY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "high_pass_input_spectrum",
                    "Input Magnitude Spectrum",
                    ImageAsset(
                        f"{Path(image.name).stem}-high-pass-input-spectrum",
                        magnitude_display(spectrum, logarithmic=True),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                MaskArtifact(
                    "high_pass_mask",
                    "High-Pass Frequency Mask",
                    ImageAsset(
                        f"{Path(image.name).stem}-high-pass-mask",
                        mask_image,
                        ColourModel.BINARY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "high_pass_filtered_spectrum",
                    "Filtered Magnitude Spectrum",
                    ImageAsset(
                        f"{Path(image.name).stem}-high-pass-filtered-spectrum",
                        magnitude_display(filtered, logarithmic=True),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "high_pass_response_signed",
                    "Signed High-Pass Response",
                    FloatingImage(
                        "high-pass-response",
                        response.astype(np.float32),
                        {**meta, "response_type": "high_pass"},
                    ),
                    exportable=False,
                ),
            ),
            metrics={
                "Cutoff Radius": radius,
                "Retained Frequency Bins": retained,
                "Retained Frequency Percentage": retained * 100.0 / mask.size,
                "Raw Response Minimum": float(response.min()),
                "Raw Response Maximum": float(response.max()),
                "Maximum Absolute Response": float(np.max(np.abs(response))),
            },
            metadata={"input_asset": image},
        )


def create_high_pass_presenter() -> object:
    from dip_workbench.ui.operations.frequency import FrequencyFilterPresenter

    return FrequencyFilterPresenter(
        "Normalized High-Pass Response",
        "high_pass_input_spectrum",
        "high_pass_mask",
        "high_pass_filtered_spectrum",
    )


HIGH_PASS_DEFINITION = OperationDefinition(
    OperationId("M07-04"),
    ModuleId.M07,
    "Frequency-Domain High-Pass Filter",
    "Apply an ideal circular high-pass filter in the Fourier domain.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "cutoff_percent",
            "Cutoff Percent",
            ParameterType.FLOAT,
            10.0,
            minimum=1.0,
            maximum=100.0,
            step=1.0,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T3_ANALYSIS_AND_GRAPH,
    HighPassExecutor,
    create_high_pass_presenter,
)

operation_registry.register(HIGH_PASS_DEFINITION)
