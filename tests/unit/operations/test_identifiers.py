import pytest

from dip_workbench.core import InputValidationError
from dip_workbench.operations import MODULE_NAMES, ModuleId, OperationId, parse_operation_id


def test_modules_and_valid_id() -> None:
    assert len(ModuleId) == 10 and len(MODULE_NAMES) == 10
    value = OperationId("M10-11")
    assert (
        value.module_id is ModuleId.M10
        and value.sequence == 11
        and str(value) == "M10-11"
        and parse_operation_id(value) is value
    )


@pytest.mark.parametrize(
    "value", ["M00-01", "M11-01", "M12-01", "M01-00", "M1-01", "m01-01", " M01-01", 1]
)
def test_invalid_ids(value: object) -> None:
    with pytest.raises(InputValidationError):
        parse_operation_id(value)  # type: ignore[arg-type]
