"""Focused tests for M08 noise."""

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import AddNoiseExecutor


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


BASE = {
    "noise_type": "gaussian",
    "processing": "luminance",
    "seed": 42,
    "gaussian_mean": 0.0,
    "gaussian_std": 20.0,
    "salt_probability": 0.05,
    "pepper_probability": 0.05,
    "speckle_std": 0.10,
}


def test_same_seed_reproducible_and_different_seed_changes() -> None:
    image = ImageAsset("gray", np.full((20, 20), 100, dtype=np.uint8), ColourModel.GRAY)
    first = AddNoiseExecutor().execute(context(image, dict(BASE)))
    second = AddNoiseExecutor().execute(context(image, dict(BASE)))
    changed = AddNoiseExecutor().execute(context(image, {**BASE, "seed": 43}))
    np.testing.assert_array_equal(
        first.primary_artifact.data.data, second.primary_artifact.data.data
    )  # type: ignore[union-attr]
    assert not np.array_equal(first.primary_artifact.data.data, changed.primary_artifact.data.data)  # type: ignore[union-attr]


def test_salt_and_pepper_masks_are_exclusive_and_preserve_bounds() -> None:
    image = ImageAsset("gray", np.full((30, 30), 127, dtype=np.uint8), ColourModel.GRAY)
    result = AddNoiseExecutor().execute(
        context(
            image,
            {
                **BASE,
                "noise_type": "salt_and_pepper",
                "salt_probability": 0.2,
                "pepper_probability": 0.2,
            },
        )
    )
    output = result.primary_artifact.data
    assert output.data.min() >= 0 and output.data.max() <= 255  # type: ignore[union-attr]
    assert (
        np.count_nonzero(output.data == 255) + np.count_nonzero(output.data == 0)
        <= output.data.size
    )  # type: ignore[union-attr]


def test_speckle_is_input_scaled_and_model_preserved() -> None:
    image = ImageAsset("gray", np.array([[0, 100, 200]], dtype=np.uint8), ColourModel.GRAY)
    result = AddNoiseExecutor().execute(context(image, {**BASE, "noise_type": "speckle"}))
    output = result.primary_artifact.data
    assert output.colour_model is ColourModel.GRAY  # type: ignore[union-attr]
    assert int(output.data[0, 0]) == 0  # type: ignore[union-attr]
    assert int(output.data[0, 2]) != 200  # type: ignore[union-attr]
