import pytest

from dip_workbench.core import InputValidationError, ParameterValidationError
from dip_workbench.operations import (
    ConditionOperator,
    ParameterChoice,
    ParameterCondition,
    ParameterSpec,
    ParameterType,
    validate_parameter_values,
)


def test_parameter_types_conditions_and_schema() -> None:
    enabled = ParameterSpec("enabled", "Enabled", ParameterType.BOOLEAN, False)
    amount = ParameterSpec(
        "amount",
        "Amount",
        ParameterType.INTEGER,
        2,
        minimum=1,
        maximum=5,
        visible_when=ParameterCondition("enabled", ConditionOperator.TRUTHY),
    )
    resolved = validate_parameter_values((enabled, amount), {"enabled": True})
    assert resolved["amount"] == 2 and amount.is_visible(resolved)
    with pytest.raises(TypeError):
        resolved["x"] = 1  # type: ignore[index]
    with pytest.raises(ParameterValidationError):
        amount.validate(True, {})


def test_choices_ranges_lists_kernel_and_custom_validator() -> None:
    choice = ParameterSpec(
        "mode",
        "Mode",
        ParameterType.ENUM,
        "a",
        choices=(ParameterChoice("a", "A"), ParameterChoice("b", "B")),
    )
    choice.validate("b", {})
    ParameterSpec("range", "Range", ParameterType.INTEGER_RANGE, (0, 1)).validate((0, 2), {})
    ParameterSpec("kernel", "Kernel", ParameterType.KERNEL, ((1, 2), (3, 4))).validate(((1,),), {})
    custom = ParameterSpec(
        "odd",
        "Odd",
        ParameterType.INTEGER,
        1,
        validator=lambda value, values: "must be odd" if value % 2 == 0 else None,
    )  # type: ignore[operator]
    with pytest.raises(ParameterValidationError):
        custom.validate(2, {})
    with pytest.raises(InputValidationError):
        ParameterSpec("bad", "Bad", ParameterType.INTEGER, True)
    with pytest.raises(ParameterValidationError):
        validate_parameter_values((choice,), {"unknown": 1})
