import pytest

from dip_workbench.core import ColourModel, InputValidationError
from dip_workbench.operations import InputSpec


def test_valid_single_image_input_contract() -> None:
    spec = InputSpec(
        "image",
        "Image",
        accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
    )
    assert spec.allow_original and spec.allow_current
    assert spec.accepted_colour_models == frozenset({ColourModel.RGB, ColourModel.GRAY})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"key": "Bad"},
        {"label": ""},
        {"accepted_colour_models": frozenset({"RGB"})},
        {"allow_original": False, "allow_current": False},
    ],
)
def test_invalid_inputs(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {"key": "image", "label": "Image"}
    values.update(kwargs)
    with pytest.raises(InputValidationError):
        InputSpec(**values)  # type: ignore[arg-type]
