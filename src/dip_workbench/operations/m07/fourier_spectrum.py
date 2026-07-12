"""M07-01 Fourier Magnitude Spectrum."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.m07.common import grayscale_float, magnitude_display, phase_display
from dip_workbench.operations.parameters import ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext


class FourierSpectrumExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Fourier spectrum requires RGB or grayscale input.")
        gray = grayscale_float(image)
        context.cancellation_token.raise_if_cancelled()
        raw = np.fft.fft2(gray)
        spectrum = np.fft.fftshift(raw) if context.parameters.get("center_spectrum") else raw
        magnitude = np.abs(spectrum)
        mag_image = magnitude_display(
            spectrum, logarithmic=bool(context.parameters.get("logarithmic_scale"))
        )
        context.cancellation_token.raise_if_cancelled()
        meta = {
            "operation_id": "M07-01",
            "input_asset_id": image.id,
            **dict(context.parameters),
            "colour_conversion": "RGB2GRAY" if image.colour_model is ColourModel.RGB else "none",
        }
        artifacts = []
        if context.parameters.get("show_phase"):
            artifacts.append(
                ImageArtifact(
                    "fourier_phase",
                    "Fourier Phase Spectrum",
                    ImageAsset(
                        f"{Path(image.name).stem}-phase",
                        phase_display(spectrum),
                        ColourModel.GRAY,
                        source_path=image.source_path,
                        metadata=meta,
                    ),
                )
            )
        return OperationResult(
            ImageArtifact(
                "fourier_magnitude",
                "Fourier Magnitude Spectrum",
                ImageAsset(
                    f"{Path(image.name).stem}-fourier",
                    mag_image,
                    ColourModel.GRAY,
                    source_path=image.source_path,
                    metadata=meta,
                ),
            ),
            tuple(artifacts),
            metrics={
                "Minimum Magnitude": float(magnitude.min()),
                "Maximum Magnitude": float(magnitude.max()),
                "Mean Magnitude": float(magnitude.mean()),
            },
            metadata={"input_asset": image},
        )


def create_fourier_presenter() -> object:
    from dip_workbench.ui.operations.frequency import FourierSpectrumPresenter

    return FourierSpectrumPresenter()


FOURIER_SPECTRUM_DEFINITION = OperationDefinition(
    OperationId("M07-01"),
    ModuleId.M07,
    "Fourier Magnitude Spectrum",
    "Display Fourier magnitude and optional phase spectra.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec("center_spectrum", "Center Spectrum", ParameterType.BOOLEAN, True),
        ParameterSpec("logarithmic_scale", "Logarithmic Scale", ParameterType.BOOLEAN, True),
        ParameterSpec("show_phase", "Show Phase", ParameterType.BOOLEAN, False),
    ),
    PreviewPolicy.DEBOUNCED,
    ApplyPolicy.NONE,
    PresenterId.T3_ANALYSIS_AND_GRAPH,
    FourierSpectrumExecutor,
    create_fourier_presenter,
    (
        "fourier transform",
        "fft",
        "magnitude spectrum",
        "frequency spectrum",
        "phase spectrum",
        "frequency analysis",
    ),
)

operation_registry.register(FOURIER_SPECTRUM_DEFINITION)
