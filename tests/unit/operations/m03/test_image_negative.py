"""Material tests for M03-01 Image Negative."""

import numpy as np
import pytest

from dip_workbench.core import CancelledOperation, ColourModel, ImageAsset, InputValidationError
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    ApplyPolicy,
    ImageNegativeExecutor,
    ModuleId,
    PreviewPolicy,
    operation_registry,
)


def execute(asset: ImageAsset, handling: str = "luminance"):
    return ImageNegativeExecutor().execute(
        OperationContext(
            {"image": asset},
            {"colour_handling": handling},
            {},
            {},
            CancellationToken(),
            lambda percent, message: None,
        )
    )


def test_definition_and_registry_contract() -> None:
    definitions = operation_registry.all()
    assert len(definitions) == 11
    definition = operation_registry.get("M03-01")
    assert str(definition.id) == "M03-01"
    assert definition.module_id is ModuleId.M03
    assert definition.preview_policy is PreviewPolicy.IMMEDIATE
    assert definition.apply_policy is ApplyPolicy.PRIMARY_ARTIFACT
    assert definition.input_spec[0].key == "image"
    assert definition.parameter_schema[0].default == "luminance"


def test_grayscale_inversion_shape_model_and_input_immutability() -> None:
    source = np.array([[0, 127, 255], [20, 40, 60]], dtype=np.uint8)
    asset = ImageAsset(name="gray.png", data=source, colour_model=ColourModel.GRAY)
    before = asset.data.copy()
    result = execute(asset)
    output = result.primary_artifact.data
    assert isinstance(output, ImageAsset)
    assert output.colour_model is ColourModel.GRAY
    assert output.shape == source.shape
    assert output.data[0].tolist() == [255, 128, 0]
    assert np.array_equal(asset.data, before)


def test_rgb_channels_are_exact_and_involution() -> None:
    source = np.array([[[0, 10, 255], [100, 127, 200]]], dtype=np.uint8)
    asset = ImageAsset(name="rgb", data=source, colour_model=ColourModel.RGB)
    first = execute(asset, "channels").primary_artifact.data
    assert isinstance(first, ImageAsset)
    assert np.array_equal(first.data, 255 - source)
    second = execute(first, "channels").primary_artifact.data
    assert isinstance(second, ImageAsset)
    assert np.array_equal(second.data, source)


def test_rgb_luminance_and_grayscale_output() -> None:
    source = ImageAsset(
        name="colour",
        data=np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]]], dtype=np.uint8),
        colour_model=ColourModel.RGB,
    )
    luminance = execute(source).primary_artifact.data
    grayscale = execute(source, "grayscale").primary_artifact.data
    assert isinstance(luminance, ImageAsset) and luminance.colour_model is ColourModel.RGB
    assert luminance.shape == source.shape and luminance.data.flags.c_contiguous
    assert isinstance(grayscale, ImageAsset) and grayscale.colour_model is ColourModel.GRAY
    assert grayscale.shape == source.shape[:2]


def test_curve_mapping_metadata_and_validation() -> None:
    asset = ImageAsset(
        name="gray", data=np.zeros((2, 2), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    result = execute(asset)
    curve = result.get_artifact("mapping_curve").data
    assert curve["input"][[0, 127, 255]].tolist() == [0, 127, 255]
    assert curve["output"][[0, 127, 255]].tolist() == [255, 128, 0]
    output = result.primary_artifact.data
    assert isinstance(output, ImageAsset)
    assert output.metadata["operation_id"] == "M03-01"
    with pytest.raises(InputValidationError):
        execute(asset, "invalid")
    binary = ImageAsset(
        name="binary", data=np.zeros((2, 2), dtype=np.uint8), colour_model=ColourModel.BINARY
    )
    with pytest.raises(InputValidationError):
        execute(binary)


def test_cancellation_is_checked() -> None:
    token = CancellationToken()
    token.cancel()
    asset = ImageAsset(
        name="gray", data=np.zeros((2, 2), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    with pytest.raises(CancelledOperation):
        ImageNegativeExecutor().execute(
            OperationContext(
                {"image": asset},
                {"colour_handling": "luminance"},
                {},
                {},
                token,
                lambda percent, message: None,
            )
        )
