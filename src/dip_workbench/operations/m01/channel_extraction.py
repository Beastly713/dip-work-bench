"""M01-03 Colour-Channel Extraction."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

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
from dip_workbench.operations.parameters import ParameterChoice, ParameterSpec, ParameterType
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import ApplyCandidate, OperationResult

if TYPE_CHECKING:
    from dip_workbench.execution.contracts import OperationContext

CHANNELS: tuple[Literal["red", "green", "blue"], ...] = ("red", "green", "blue")
CHANNEL_CHOICES = (
    ParameterChoice("all", "All"),
    ParameterChoice("red", "Red"),
    ParameterChoice("green", "Green"),
    ParameterChoice("blue", "Blue"),
)
DISPLAY_CHOICES = (
    ParameterChoice("intensity", "Intensity"),
    ParameterChoice("isolated_colour", "Isolated colour"),
)


def _channel_asset(
    image: ImageAsset, channel: Literal["red", "green", "blue"], display: object
) -> ImageAsset:
    index = {"red": 0, "green": 1, "blue": 2}[channel]
    values = image.data[..., index]
    if display == "isolated_colour":
        output = np.zeros_like(image.data)
        output[..., index] = values
        model = ColourModel.RGB
    else:
        output = np.array(values, copy=True, order="C")
        model = ColourModel.GRAY
    return ImageAsset(
        name=f"{Path(image.name).stem}-{channel}-channel",
        data=np.ascontiguousarray(output, dtype=np.uint8),
        colour_model=model,
        source_path=image.source_path,
        metadata={
            "operation_id": "M01-03",
            "input_asset_id": image.id,
            "channel": channel,
            "display": display,
        },
    )


class ChannelExtractionExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model is not ColourModel.RGB:
            raise InputValidationError("Colour-Channel Extraction requires an RGB image.")
        channel = context.parameters.get("channel")
        display = context.parameters.get("display")
        if channel not in {"all", *CHANNELS} or display not in {
            choice.value for choice in DISPLAY_CHOICES
        }:
            raise InputValidationError("Channel extraction parameters are invalid.")
        selected = (
            CHANNELS if channel == "all" else (cast(Literal["red", "green", "blue"], channel),)
        )
        artifacts = tuple(
            ImageArtifact(
                f"{item}_channel",
                f"{item.title()} Channel",
                _channel_asset(image, item, display),
            )
            for item in selected
        )
        candidates = tuple(ApplyCandidate(artifact.key, artifact.label) for artifact in artifacts)
        return OperationResult(
            artifacts[0],
            artifacts[1:],
            metadata={"input_asset": image, "channel_mode": channel},
            apply_candidates=candidates,
        )


def create_channel_extraction_presenter() -> object:
    from dip_workbench.ui.operations.fundamentals import ChannelExtractionPresenter

    return ChannelExtractionPresenter()


CHANNEL_EXTRACTION_DEFINITION = OperationDefinition(
    OperationId("M01-03"),
    ModuleId.M01,
    "Colour-Channel Extraction",
    "Extract red, green and blue channels from an RGB image.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB}),
        ),
    ),
    (
        ParameterSpec(
            "channel",
            "Channel",
            ParameterType.ENUM,
            "all",
            choices=CHANNEL_CHOICES,
        ),
        ParameterSpec(
            "display",
            "Display",
            ParameterType.ENUM,
            "intensity",
            choices=DISPLAY_CHOICES,
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.EXPLICIT_CANDIDATES,
    PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
    ChannelExtractionExecutor,
    create_channel_extraction_presenter,
    (
        "rgb channels",
        "red channel",
        "green channel",
        "blue channel",
        "split channels",
        "channel extraction",
    ),
)

operation_registry.register(CHANNEL_EXTRACTION_DEFINITION)
