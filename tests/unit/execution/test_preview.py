import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.execution import PreviewInputReducer, PreviewResolutionPolicy


def asset(model: ColourModel, width: int = 2000, height: int = 1000) -> ImageAsset:
    data = (
        np.zeros((height, width, 3), dtype=np.uint8)
        if model is ColourModel.RGB
        else np.zeros((height, width), dtype=np.uint8)
    )
    if model is ColourModel.BINARY:
        data[:, ::2] = 255
    return ImageAsset(name="x", data=data, colour_model=model)


@pytest.mark.parametrize("model", [ColourModel.RGB, ColourModel.GRAY, ColourModel.BINARY])
def test_reduce_models_aspect_metadata_and_source_immutability(model: ColourModel) -> None:
    source = asset(model)
    reduced = PreviewInputReducer(PreviewResolutionPolicy(maximum_dimension=100)).reduce_inputs(
        {"nested": [source]}
    )["nested"][0]  # type: ignore[index]
    assert (
        reduced.shape[:2] == (50, 100)
        and reduced.id != source.id
        and reduced.metadata["preview_original_asset_id"] == source.id
    )
    if model is ColourModel.BINARY:
        assert set(np.unique(reduced.data)) <= {0, 255}
    assert source.shape[:2] == (1000, 2000)


def test_small_and_disabled_are_retained() -> None:
    small = asset(ColourModel.GRAY, 20, 10)
    assert PreviewInputReducer(PreviewResolutionPolicy()).reduce_inputs({"x": small})["x"] is small
    large = asset(ColourModel.GRAY)
    assert (
        PreviewInputReducer(PreviewResolutionPolicy(enabled=False)).reduce_inputs({"x": large})["x"]
        is large
    )
    with pytest.raises(InputValidationError):
        PreviewResolutionPolicy(maximum_dimension=0)
