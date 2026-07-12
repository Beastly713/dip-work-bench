"""M07-03 Frequency-Domain Low-Pass Filter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
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
    clipped_reconstruction,
    grayscale_float,
    inverse_shifted_fft,
    magnitude_display,
    shifted_fft,
)
from dip_workbench.operations.m10.common import number
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


class LowPassExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Low-pass filtering requires RGB or grayscale input.")
        cutoff = number(context.parameters["cutoff_percent"], "Cutoff percent")
        gray = grayscale_float(image)
        context.cancellation_token.raise_if_cancelled()
        spectrum = shifted_fft(gray)
        context.cancellation_token.raise_if_cancelled()
        mask, radius = circular_frequency_mask(gray.shape, cutoff, pass_type="low")
        filtered = spectrum * mask
        reconstruction = inverse_shifted_fft(filtered)
        context.cancellation_token.raise_if_cancelled()
        result = clipped_reconstruction(reconstruction)
        mask_image = np.where(mask, 255, 0).astype(np.uint8)
        retained = int(np.count_nonzero(mask))
        meta = {
            "operation_id": "M07-03",
            "input_asset_id": image.id,
            "filter_type": "ideal_low_pass",
            "cutoff_percent": cutoff,
            "cutoff_radius": radius,
            "display_mapping": "clipped",
            "colour_conversion": "RGB2GRAY" if image.colour_model is ColourModel.RGB else "none",
        }
        return OperationResult(
            ImageArtifact(
                "low_pass_result",
                "Low-Pass Filtered Image",
                ImageAsset(
                    f"{Path(image.name).stem}-low-pass",
                    result,
                    ColourModel.GRAY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            (
                ImageArtifact(
                    "low_pass_input_spectrum",
                    "Input Magnitude Spectrum",
                    ImageAsset(
                        f"{Path(image.name).stem}-low-pass-input-spectrum",
                        magnitude_display(spectrum, logarithmic=True),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                MaskArtifact(
                    "low_pass_mask",
                    "Low-Pass Frequency Mask",
                    ImageAsset(
                        f"{Path(image.name).stem}-low-pass-mask",
                        mask_image,
                        ColourModel.BINARY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
                ImageArtifact(
                    "low_pass_filtered_spectrum",
                    "Filtered Magnitude Spectrum",
                    ImageAsset(
                        f"{Path(image.name).stem}-low-pass-filtered-spectrum",
                        magnitude_display(filtered, logarithmic=True),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                ),
            ),
            metrics={
                "Cutoff Radius": radius,
                "Retained Frequency Bins": retained,
                "Retained Frequency Percentage": retained * 100.0 / mask.size,
                "Raw Reconstruction Minimum": float(reconstruction.min()),
                "Raw Reconstruction Maximum": float(reconstruction.max()),
            },
            metadata={"input_asset": image},
        )


def create_low_pass_presenter() -> object:
    from dip_workbench.ui.operations.frequency import FrequencyFilterPresenter

    return FrequencyFilterPresenter(
        "low_pass_result",
        "Low-Pass Filtered Image",
        "low_pass_input_spectrum",
        "low_pass_mask",
        "low_pass_filtered_spectrum",
    )


LOW_PASS_DEFINITION = OperationDefinition(
    OperationId("M07-03"),
    ModuleId.M07,
    "Frequency-Domain Low-Pass Filter",
    "Apply an ideal circular low-pass filter in the Fourier domain.",
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
            15.0,
            minimum=1.0,
            maximum=100.0,
            step=1.0,
        ),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T3_ANALYSIS_AND_GRAPH,
    LowPassExecutor,
    create_low_pass_presenter,
)

operation_registry.register(LOW_PASS_DEFINITION)
