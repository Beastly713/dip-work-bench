import pytest

from dip_workbench.core import ColourModel, InputValidationError
from dip_workbench.operations import InputRole, InputSpec


def test_valid_input_contracts() -> None:
    spec = InputSpec(
        "primary_image",
        "Primary",
        InputRole.PRIMARY_IMAGE,
        accepted_colour_models=frozenset({ColourModel.RGB}),
    )
    assert spec.accepted_colour_models == frozenset({ColourModel.RGB})
    dataset = InputSpec(
        "images", "Images", InputRole.DATASET, multiple=True, minimum_count=2, maximum_count=None
    )
    assert dataset.multiple


@pytest.mark.parametrize(
    "kwargs",
    [
        {"key": "Bad"},
        {"label": ""},
        {"minimum_count": 0},
        {"maximum_count": 0},
        {"allow_original": False, "allow_current": False},
    ],
)
def test_invalid_inputs(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "key": "primary_image",
        "label": "Primary",
        "role": InputRole.PRIMARY_IMAGE,
    }
    values.update(kwargs)
    with pytest.raises(InputValidationError):
        InputSpec(**values)  # type: ignore[arg-type]
